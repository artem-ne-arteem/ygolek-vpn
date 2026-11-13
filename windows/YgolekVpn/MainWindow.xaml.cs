using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Net.Http;
using System.Windows;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using QRCoder;
using YgolekVpn.Services;

namespace YgolekVpn;

public partial class MainWindow : Window
{
    private const string SupportUrl = "https://t.me/ygolek_support";

    private readonly ApiClient _api = new();
    private readonly SingBoxRunner _core = new();
    private CancellationTokenSource? _loginCts;
    private string? _token;
    private Account? _account;
    private string? _loginBotUrl;

    public MainWindow()
    {
        InitializeComponent();
        _core.Exited += code => Dispatcher.Invoke(() =>
        {
            SetConnected(false);
            ShowError($"Соединение прервалось: {SingBoxRunner.LastLogLine() ?? $"код {code}"}");
        });
        Loaded += async (_, _) => await StartAsync();
    }

    private async Task StartAsync()
    {
        _token = AppStorage.LoadToken();
        if (_token == null) await ShowLoginAsync();
        else await ShowHomeAsync();
    }

    // ---------- Вход ----------

    private async Task ShowLoginAsync()
    {
        HomePanel.Visibility = Visibility.Collapsed;
        LogoutButton.Visibility = Visibility.Collapsed;
        LoginPanel.Visibility = Visibility.Visible;
        NewCodeButton.Visibility = Visibility.Collapsed;
        HideError();

        _loginCts?.Cancel();
        var cts = _loginCts = new CancellationTokenSource();

        LoginStart start;
        try
        {
            start = await _api.StartLoginAsync($"Windows · {Environment.MachineName}");
        }
        catch (HttpRequestException)
        {
            LoginStatus.Text = "Нет связи с сервером. Проверь интернет.";
            NewCodeButton.Visibility = Visibility.Visible;
            return;
        }

        _loginBotUrl = start.BotUrl;
        QrImage.Source = RenderQr(start.BotUrl);
        LoginStatus.Text = "Ждём подтверждения в боте…";

        var deadline = DateTime.UtcNow.AddSeconds(start.ExpiresIn);
        while (!cts.IsCancellationRequested && DateTime.UtcNow < deadline)
        {
            await Task.Delay(2000);
            if (cts.IsCancellationRequested) return;

            LoginPoll poll;
            try
            {
                poll = await _api.PollLoginAsync(start.Code, start.Secret);
            }
            catch (HttpRequestException)
            {
                continue; // временная ошибка сети — пробуем дальше
            }

            switch (poll.Status)
            {
                case "ok" when poll.Token != null:
                    _token = poll.Token;
                    AppStorage.SaveToken(poll.Token);
                    await ShowHomeAsync();
                    return;
                case "denied":
                    LoginStatus.Text = "Вход отменён в боте.";
                    NewCodeButton.Visibility = Visibility.Visible;
                    return;
                case "expired":
                case "invalid":
                    deadline = DateTime.MinValue;
                    break;
            }
        }

        if (!cts.IsCancellationRequested)
        {
            LoginStatus.Text = "Код устарел.";
            NewCodeButton.Visibility = Visibility.Visible;
        }
    }

    private static BitmapImage RenderQr(string text)
    {
        using var generator = new QRCodeGenerator();
        using var data = generator.CreateQrCode(text, QRCodeGenerator.ECCLevel.M);
        var png = new PngByteQRCode(data).GetGraphic(10);
        var image = new BitmapImage();
        image.BeginInit();
        image.StreamSource = new MemoryStream(png);
        image.CacheOption = BitmapCacheOption.OnLoad;
        image.EndInit();
        return image;
    }

    private void OpenTelegram_Click(object sender, RoutedEventArgs e)
    {
        if (_loginBotUrl != null) OpenUrl(_loginBotUrl);
    }

    private async void NewCode_Click(object sender, RoutedEventArgs e) => await ShowLoginAsync();

    // ---------- Главный экран ----------

    private async Task ShowHomeAsync()
    {
        LoginPanel.Visibility = Visibility.Collapsed;
        HomePanel.Visibility = Visibility.Visible;
        LogoutButton.Visibility = Visibility.Visible;
        HideError();
        SubscriptionTitle.Text = "Загрузка…";
        SubscriptionDetails.Text = "";
        ConnectButton.IsEnabled = false;

        try
        {
            _account = await _api.GetAccountAsync(_token!);
        }
        catch (HttpRequestException)
        {
            SubscriptionTitle.Text = "Нет связи с сервером";
            SubscriptionDetails.Text = "Проверь интернет и перезапусти приложение.";
            return;
        }

        if (_account == null)
        {
            // токен отозван — входим заново
            AppStorage.DeleteToken();
            _token = null;
            await ShowLoginAsync();
            return;
        }

        LogoutText.Text = _account.Username != null ? $"@{_account.Username} · Выйти" : "Выйти";

        if (_account.Subscription == null || _account.Key == null)
        {
            SubscriptionTitle.Text = "Нет активной подписки";
            SubscriptionDetails.Text = "Оформи подписку в боте — после оплаты перезапусти приложение.";
            RenewButton.Content = "Оформить подписку";
            ServerBox.ItemsSource = null;
            return;
        }

        var expires = _account.Subscription.ExpiresAt.ToLocalTime();
        var daysLeft = Math.Max(0, (int)Math.Ceiling((expires - DateTime.Now).TotalDays));
        SubscriptionTitle.Text = $"Активна до {expires:dd.MM.yyyy}";
        SubscriptionDetails.Text = $"Осталось {daysLeft} дн. · до {_account.DeviceLimit} устройств";
        RenewButton.Content = "Продлить подписку";

        try
        {
            var servers = await SubscriptionLoader.LoadAsync(_account.Key);
            ServerBox.ItemsSource = servers;
            ServerBox.SelectedIndex = servers.Count > 0 ? 0 : -1;
            ConnectButton.IsEnabled = servers.Count > 0;
            if (servers.Count == 0) ShowError("В подписке нет серверов. Напиши в поддержку.");
        }
        catch (HttpRequestException)
        {
            ShowError("Не удалось загрузить список серверов. Проверь интернет.");
        }
    }

    private async void Connect_Click(object sender, RoutedEventArgs e)
    {
        HideError();
        if (_core.IsRunning)
        {
            _core.Stop();
            SetConnected(false);
            return;
        }

        if (ServerBox.SelectedItem is not VlessLink link) return;
        ConnectButton.IsEnabled = false;
        ConnectionStatus.Text = "Подключение…";
        try
        {
            await _core.StartAsync(link);
            SetConnected(true);
        }
        catch (Exception ex)
        {
            SetConnected(false);
            ShowError(ex.Message);
        }
        finally
        {
            ConnectButton.IsEnabled = true;
        }
    }

    private void SetConnected(bool connected)
    {
        ConnectButton.Content = connected ? "Отключить" : "Подключить";
        ConnectButton.Background = (Brush)FindResource(connected ? "Success" : "Accent");
        ConnectionStatus.Text = connected ? $"Подключено · {(ServerBox.SelectedItem as VlessLink)?.Name}" : "Не подключено";
        ServerBox.IsEnabled = !connected;
    }

    private void Renew_Click(object sender, RoutedEventArgs e)
    {
        if (_account != null) OpenUrl(_account.Subscription == null ? _account.BotUrl : _account.RenewUrl);
    }

    private async void Logout_Click(object sender, RoutedEventArgs e)
    {
        _core.Stop();
        SetConnected(false);
        if (_token != null) await _api.LogoutAsync(_token);
        AppStorage.DeleteToken();
        _token = null;
        _account = null;
        await ShowLoginAsync();
    }

    private void Support_Click(object sender, RoutedEventArgs e) => OpenUrl(SupportUrl);

    // ---------- Общее ----------

    protected override void OnClosing(CancelEventArgs e)
    {
        _loginCts?.Cancel();
        _core.Stop();
        base.OnClosing(e);
    }

    private void ShowError(string text)
    {
        ErrorText.Text = text;
        ErrorText.Visibility = Visibility.Visible;
    }

    private void HideError() => ErrorText.Visibility = Visibility.Collapsed;

    private static void OpenUrl(string url) => Process.Start(new ProcessStartInfo(url) { UseShellExecute = true });
}

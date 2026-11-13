using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Net.Http;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Media.Imaging;
using System.Windows.Threading;
using QRCoder;
using YgolekVpn.Services;

namespace YgolekVpn;

public partial class MainWindow : Window
{
    private const string SupportUrl = "https://t.me/ygolek_support";

    private enum ConnectionState { Off, Connecting, On }

    private readonly ApiClient _api = new();
    private readonly SingBoxRunner _core = new();
    private readonly DispatcherTimer _clock = new() { Interval = TimeSpan.FromSeconds(1) };
    private CancellationTokenSource? _loginCts;
    private string? _token;
    private Account? _account;
    private string? _loginBotUrl;
    private DateTime _connectedAt;

    public MainWindow()
    {
        InitializeComponent();
        _clock.Tick += (_, _) => UpdateConnectedTime();
        _core.Exited += code => Dispatcher.Invoke(() =>
        {
            SetState(ConnectionState.Off);
            ShowError($"Соединение прервалось: {SingBoxRunner.LastLogLine() ?? $"код {code}"}");
        });
        ServerList.SelectionChanged += (_, _) =>
        {
            if (ServerList.SelectedItem is VlessLink link) AppStorage.LastServer = link.Name;
        };
        Loaded += async (_, _) => await StartAsync();
    }

    protected override void OnSourceInitialized(EventArgs e)
    {
        base.OnSourceInitialized(e);
        UseDarkTitleBar();
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
        StatusPill.Visibility = Visibility.Collapsed;
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
            SetLoginStatus("Нет связи с сервером. Проверь интернет.", waiting: false);
            NewCodeButton.Visibility = Visibility.Visible;
            return;
        }

        _loginBotUrl = start.BotUrl;
        QrImage.Source = RenderQr(start.BotUrl);
        SetLoginStatus("Ждём подтверждения в боте…", waiting: true);

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
                    SetLoginStatus("Вход отменён в боте.", waiting: false);
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
            SetLoginStatus("Код устарел.", waiting: false);
            NewCodeButton.Visibility = Visibility.Visible;
        }
    }

    private void SetLoginStatus(string text, bool waiting)
    {
        LoginStatus.Text = text;
        LoginDot.Fill = (Brush)FindResource(waiting ? "Accent2" : "Muted");
        LoginDot.BeginAnimation(OpacityProperty, waiting ? Pulse(1, 0.25, 0.8) : null);
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
        StatusPill.Visibility = Visibility.Visible;
        HideError();
        SetState(ConnectionState.Off);
        SubscriptionTitle.Text = "Загрузка…";
        SubscriptionDetails.Text = "";
        DaysBar.Value = 0;
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
            SubscriptionDetails.Text = "Оформи в боте, затем перезапусти приложение";
            RenewButton.Content = "Оформить";
            ShowServers([]);
            ConnectionStatus.Text = "Нужна активная подписка";
            return;
        }

        var expires = _account.Subscription.ExpiresAt.ToLocalTime();
        var daysLeft = Math.Max(0, (int)Math.Ceiling((expires - DateTime.Now).TotalDays));
        SubscriptionTitle.Text = $"Активна до {expires:dd.MM.yyyy}";
        SubscriptionDetails.Text = $"Осталось {DaysLabel(daysLeft)} · до {_account.DeviceLimit} устройств";
        DaysBar.Value = Math.Min(daysLeft, DaysBar.Maximum);
        DaysBar.Foreground = (Brush)FindResource(daysLeft <= 3 ? "Danger" : "Accent");
        RenewButton.Content = "Продлить";

        try
        {
            var servers = await SubscriptionLoader.LoadAsync(_account.Key);
            ShowServers(servers);
            if (servers.Count == 0) ShowError("В подписке нет серверов. Напиши в поддержку.");
        }
        catch (HttpRequestException)
        {
            ShowServers([]);
            ShowError("Не удалось загрузить список серверов. Проверь интернет.");
        }
    }

    private void ShowServers(List<VlessLink> servers)
    {
        ServerList.ItemsSource = servers;
        ServerList.SelectedItem = servers.FirstOrDefault(s => s.Name == AppStorage.LastServer) ?? servers.FirstOrDefault();
        ServersEmpty.Visibility = servers.Count == 0 ? Visibility.Visible : Visibility.Collapsed;
        ConnectButton.IsEnabled = servers.Count > 0;
    }

    private async void Connect_Click(object sender, RoutedEventArgs e)
    {
        HideError();
        if (_core.IsRunning)
        {
            _core.Stop();
            SetState(ConnectionState.Off);
            return;
        }

        if (ServerList.SelectedItem is not VlessLink link) return;
        SetState(ConnectionState.Connecting);
        try
        {
            await _core.StartAsync(link);
            SetState(ConnectionState.On);
        }
        catch (Exception ex)
        {
            SetState(ConnectionState.Off);
            ShowError(ex.Message);
        }
    }

    private void SetState(ConnectionState state)
    {
        var color = state switch
        {
            ConnectionState.On => (Color)FindResource("SuccessColor"),
            _ => (Color)FindResource("AccentColor"),
        };
        var brush = new SolidColorBrush(color);

        ConnectButton.Background = state == ConnectionState.On ? brush : (Brush)FindResource("Panel2");
        ConnectButton.BorderBrush = brush;
        ConnectButton.IsEnabled = state != ConnectionState.Connecting && ServerList.Items.Count > 0;
        ConnectButton.ToolTip = state == ConnectionState.On ? "Отключить" : "Подключить";
        GlowEffect.Color = color;
        Glow.BeginAnimation(OpacityProperty, state switch
        {
            ConnectionState.Connecting => Pulse(0.75, 0.2, 0.7),
            _ => null,
        });
        Glow.Opacity = state == ConnectionState.On ? 0.75 : 0.35;

        ServerList.IsEnabled = state == ConnectionState.Off;
        var server = (ServerList.SelectedItem as VlessLink)?.DisplayName;

        switch (state)
        {
            case ConnectionState.Off:
                _clock.Stop();
                ConnectionTitle.Text = "Не подключено";
                ConnectionStatus.Text = ServerList.Items.Count > 0 ? "Выбери сервер и нажми кнопку" : ConnectionStatus.Text;
                SetPill("Отключено", "Muted");
                break;
            case ConnectionState.Connecting:
                ConnectionTitle.Text = "Подключение…";
                ConnectionStatus.Text = server ?? "";
                SetPill("Подключение", "Accent2");
                break;
            case ConnectionState.On:
                _connectedAt = DateTime.Now;
                _clock.Start();
                ConnectionTitle.Text = "Подключено";
                UpdateConnectedTime();
                SetPill("Защищено", "Success");
                break;
        }
    }

    private void UpdateConnectedTime()
    {
        var elapsed = DateTime.Now - _connectedAt;
        var server = (ServerList.SelectedItem as VlessLink)?.DisplayName;
        ConnectionStatus.Text = $"{server} · {(int)elapsed.TotalHours:00}:{elapsed.Minutes:00}:{elapsed.Seconds:00}";
    }

    private void SetPill(string text, string colorKey)
    {
        var brush = (Brush)FindResource(colorKey);
        StatusPillText.Text = text;
        StatusPillText.Foreground = brush;
        StatusDot.Fill = brush;
    }

    private void Renew_Click(object sender, RoutedEventArgs e)
    {
        if (_account != null) OpenUrl(_account.Subscription == null ? _account.BotUrl : _account.RenewUrl);
    }

    private async void Logout_Click(object sender, RoutedEventArgs e)
    {
        _core.Stop();
        SetState(ConnectionState.Off);
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
        ErrorBox.Visibility = Visibility.Visible;
    }

    private void HideError() => ErrorBox.Visibility = Visibility.Collapsed;

    private static string DaysLabel(int days)
    {
        var word = (days % 10, days % 100) switch
        {
            (1, not 11) => "день",
            (>= 2 and <= 4, not (>= 12 and <= 14)) => "дня",
            _ => "дней",
        };
        return $"{days} {word}";
    }

    private static DoubleAnimation Pulse(double from, double to, double seconds) =>
        new(from, to, TimeSpan.FromSeconds(seconds)) { AutoReverse = true, RepeatBehavior = RepeatBehavior.Forever };

    private static void OpenUrl(string url) => Process.Start(new ProcessStartInfo(url) { UseShellExecute = true });

    // Тёмный заголовок окна в цвет фона (Windows 10 20H1+ / Windows 11)
    private void UseDarkTitleBar()
    {
        var hwnd = new WindowInteropHelper(this).Handle;
        int on = 1;
        DwmSetWindowAttribute(hwnd, 20, ref on, sizeof(int));          // DWMWA_USE_IMMERSIVE_DARK_MODE
        int caption = 0x00170D08;                                       // #080D17 в формате 0x00BBGGRR
        DwmSetWindowAttribute(hwnd, 35, ref caption, sizeof(int));     // DWMWA_CAPTION_COLOR (Windows 11)
    }

    [DllImport("dwmapi.dll")]
    private static extern int DwmSetWindowAttribute(IntPtr hwnd, int attribute, ref int value, int size);
}

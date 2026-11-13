using System.Net.Http;
using System.Text;
using System.Web;

namespace YgolekVpn.Services;

/// <summary>Сервер из подписки: ссылка vless://uuid@host:port?параметры#название</summary>
public sealed record VlessLink(
    string Name,
    string Uuid,
    string Host,
    int Port,
    string Network,      // tcp | grpc | ws | httpupgrade
    string Security,     // reality | tls | none
    string? Sni,
    string? Fingerprint,
    string? PublicKey,
    string? ShortId,
    string? Flow,
    string? ServiceName,
    string? Path,
    string? HostHeader)
{
    public override string ToString() => Name;

    public static VlessLink? TryParse(string line)
    {
        line = line.Trim();
        if (!line.StartsWith("vless://", StringComparison.OrdinalIgnoreCase)) return null;
        if (!Uri.TryCreate(line, UriKind.Absolute, out var uri)) return null;

        var q = HttpUtility.ParseQueryString(uri.Query);
        var name = Uri.UnescapeDataString(uri.Fragment.TrimStart('#'));
        return new VlessLink(
            Name: string.IsNullOrWhiteSpace(name) ? uri.Host : name,
            Uuid: Uri.UnescapeDataString(uri.UserInfo),
            Host: uri.Host,
            Port: uri.Port,
            Network: q["type"] ?? "tcp",
            Security: q["security"] ?? "none",
            Sni: q["sni"],
            Fingerprint: q["fp"],
            PublicKey: q["pbk"],
            ShortId: q["sid"],
            Flow: q["flow"],
            ServiceName: q["serviceName"],
            Path: q["path"],
            HostHeader: q["host"]);
    }
}

public static class SubscriptionLoader
{
    private static readonly HttpClient Http = new() { Timeout = TimeSpan.FromSeconds(20) };

    /// <summary>Скачивает подписку (base64 или обычный текст со ссылками) и возвращает серверы.</summary>
    public static async Task<List<VlessLink>> LoadAsync(string subscriptionUrl)
    {
        using var req = new HttpRequestMessage(HttpMethod.Get, subscriptionUrl);
        req.Headers.UserAgent.ParseAdd($"YgolekVPN-Windows/{typeof(SubscriptionLoader).Assembly.GetName().Version}");
        // по этим заголовкам панель учитывает устройство в лимите подписки
        req.Headers.Add("x-hwid", AppStorage.DeviceId());
        req.Headers.Add("x-device-os", "Windows");
        req.Headers.Add("x-device-model", Environment.MachineName);

        var resp = await Http.SendAsync(req);
        resp.EnsureSuccessStatusCode();
        var body = (await resp.Content.ReadAsStringAsync()).Trim();

        var text = body.Contains("://") ? body : DecodeBase64(body);
        return text.Split('\n', StringSplitOptions.RemoveEmptyEntries)
            .Select(VlessLink.TryParse)
            .OfType<VlessLink>()
            .ToList();
    }

    private static string DecodeBase64(string value)
    {
        var s = value.Replace('-', '+').Replace('_', '/').Replace("\n", "").Replace("\r", "");
        s = s.PadRight(s.Length + (4 - s.Length % 4) % 4, '=');
        try
        {
            return Encoding.UTF8.GetString(Convert.FromBase64String(s));
        }
        catch (FormatException)
        {
            return "";
        }
    }
}

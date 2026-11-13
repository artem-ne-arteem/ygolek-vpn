using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json.Serialization;

namespace YgolekVpn.Services;

// API сайта для приложения (site/app/api/app/*): вход через бота и данные аккаунта.
public sealed class ApiClient
{
    public const string BaseUrl = "https://ygolek-vpn.online";

    private readonly HttpClient _http = new() { BaseAddress = new Uri(BaseUrl), Timeout = TimeSpan.FromSeconds(20) };

    public async Task<LoginStart> StartLoginAsync(string device)
    {
        var resp = await _http.PostAsJsonAsync("/api/app/login/start", new { device });
        resp.EnsureSuccessStatusCode();
        return (await resp.Content.ReadFromJsonAsync<LoginStart>())!;
    }

    public async Task<LoginPoll> PollLoginAsync(string code, string secret)
    {
        var resp = await _http.PostAsJsonAsync("/api/app/login/poll", new { code, secret });
        if (resp.StatusCode is HttpStatusCode.NotFound or HttpStatusCode.BadRequest)
            return new LoginPoll("invalid", null);
        resp.EnsureSuccessStatusCode();
        return (await resp.Content.ReadFromJsonAsync<LoginPoll>())!;
    }

    /// <returns>null — токен больше не действует (вышли из аккаунта в боте и т.п.)</returns>
    public async Task<Account?> GetAccountAsync(string token)
    {
        using var req = new HttpRequestMessage(HttpMethod.Get, "/api/app/me");
        req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
        var resp = await _http.SendAsync(req);
        if (resp.StatusCode == HttpStatusCode.Unauthorized) return null;
        resp.EnsureSuccessStatusCode();
        return await resp.Content.ReadFromJsonAsync<Account>();
    }

    public async Task LogoutAsync(string token)
    {
        using var req = new HttpRequestMessage(HttpMethod.Post, "/api/app/logout");
        req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
        try { await _http.SendAsync(req); } catch (HttpRequestException) { /* выходим локально в любом случае */ }
    }
}

public sealed record LoginStart(string Code, string Secret, string BotUrl, int ExpiresIn);

public sealed record LoginPoll(string Status, string? Token);

public sealed record Account(
    long TgId,
    string? Username,
    int DeviceLimit,
    AccountSubscription? Subscription,
    string? Key,
    string RenewUrl,
    string BotUrl);

public sealed record AccountSubscription(string PlanId, DateTime ExpiresAt);

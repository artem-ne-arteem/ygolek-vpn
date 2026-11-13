using System.Text.Json;
using System.Text.Json.Nodes;

namespace YgolekVpn.Services;

// Конфиг sing-box 1.14: весь трафик системы идёт через TUN-адаптер в выбранный
// сервер, локальная сеть — напрямую.
public static class SingBoxConfig
{
    public static string Build(VlessLink link, string logPath)
    {
        var config = new JsonObject
        {
            ["log"] = new JsonObject { ["level"] = "warn", ["output"] = logPath, ["timestamp"] = true },
            ["dns"] = new JsonObject
            {
                ["servers"] = new JsonArray
                {
                    new JsonObject { ["type"] = "https", ["tag"] = "remote", ["server"] = "1.1.1.1", ["detour"] = "proxy" },
                    new JsonObject { ["type"] = "local", ["tag"] = "local" },
                },
                ["final"] = "remote",
            },
            ["inbounds"] = new JsonArray
            {
                new JsonObject
                {
                    ["type"] = "tun",
                    ["tag"] = "tun-in",
                    ["interface_name"] = "YgolekVPN",
                    ["address"] = new JsonArray("172.19.0.1/30"),
                    ["mtu"] = 9000,
                    ["auto_route"] = true,
                    ["strict_route"] = true,
                    ["stack"] = "mixed",
                },
            },
            ["outbounds"] = new JsonArray { Outbound(link), new JsonObject { ["type"] = "direct", ["tag"] = "direct" } },
            ["route"] = new JsonObject
            {
                ["rules"] = new JsonArray
                {
                    new JsonObject { ["action"] = "sniff" },
                    new JsonObject { ["protocol"] = "dns", ["action"] = "hijack-dns" },
                    new JsonObject { ["ip_is_private"] = true, ["outbound"] = "direct" },
                },
                ["final"] = "proxy",
                ["auto_detect_interface"] = true,
                ["default_domain_resolver"] = "local",
            },
        };
        return config.ToJsonString(new JsonSerializerOptions { WriteIndented = true });
    }

    private static JsonObject Outbound(VlessLink link)
    {
        var outbound = new JsonObject
        {
            ["type"] = "vless",
            ["tag"] = "proxy",
            ["server"] = link.Host,
            ["server_port"] = link.Port,
            ["uuid"] = link.Uuid,
        };
        if (!string.IsNullOrEmpty(link.Flow)) outbound["flow"] = link.Flow;

        if (link.Security is "reality" or "tls")
        {
            var tls = new JsonObject
            {
                ["enabled"] = true,
                ["server_name"] = link.Sni ?? link.Host,
                ["utls"] = new JsonObject { ["enabled"] = true, ["fingerprint"] = link.Fingerprint ?? "chrome" },
            };
            if (link.Security == "reality")
            {
                tls["reality"] = new JsonObject
                {
                    ["enabled"] = true,
                    ["public_key"] = link.PublicKey ?? "",
                    ["short_id"] = link.ShortId ?? "",
                };
            }
            outbound["tls"] = tls;
        }

        var transport = link.Network switch
        {
            "grpc" => new JsonObject { ["type"] = "grpc", ["service_name"] = link.ServiceName ?? "" },
            "ws" => WithHost(new JsonObject { ["type"] = "ws", ["path"] = link.Path ?? "/" }, link.HostHeader, headers: true),
            "httpupgrade" => WithHost(new JsonObject { ["type"] = "httpupgrade", ["path"] = link.Path ?? "/" }, link.HostHeader, headers: false),
            _ => null,
        };
        if (transport != null) outbound["transport"] = transport;
        return outbound;
    }

    private static JsonObject WithHost(JsonObject transport, string? host, bool headers)
    {
        if (string.IsNullOrEmpty(host)) return transport;
        if (headers) transport["headers"] = new JsonObject { ["Host"] = host };
        else transport["host"] = host;
        return transport;
    }
}

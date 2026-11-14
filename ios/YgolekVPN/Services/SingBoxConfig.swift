import Foundation

/// Конфиг sing-box 1.14 для VPN-модуля: весь трафик через туннель, локальная сеть
/// напрямую. Совпадает с Windows-клиентом (windows/YgolekVpn/Services/SingBoxConfig.cs),
/// кроме TUN — на iOS адаптер создаёт система, а ядро получает его через NetworkExtension.
enum SingBoxConfig {
    static func build(_ link: VlessLink) throws -> String {
        let config: [String: Any] = [
            "log": ["level": "warn", "timestamp": true],
            "dns": [
                "servers": [
                    ["type": "https", "tag": "remote", "server": "1.1.1.1", "detour": "proxy"],
                    ["type": "local", "tag": "local"],
                ],
                "final": "remote",
            ],
            "inbounds": [
                [
                    "type": "tun",
                    "tag": "tun-in",
                    "address": ["172.19.0.1/30"],
                    "auto_route": true,
                ],
            ],
            "outbounds": [outbound(link), ["type": "direct", "tag": "direct"]],
            "route": [
                "rules": [
                    ["action": "sniff"],
                    ["protocol": "dns", "action": "hijack-dns"],
                    ["ip_is_private": true, "outbound": "direct"],
                ],
                "final": "proxy",
                "auto_detect_interface": true,
                "default_domain_resolver": "local",
            ],
        ]
        let data = try JSONSerialization.data(withJSONObject: config, options: [.sortedKeys])
        return String(data: data, encoding: .utf8)!
    }

    private static func outbound(_ link: VlessLink) -> [String: Any] {
        var outbound: [String: Any] = [
            "type": "vless",
            "tag": "proxy",
            "server": link.host,
            "server_port": link.port,
            "uuid": link.uuid,
        ]
        if let flow = link.flow, !flow.isEmpty { outbound["flow"] = flow }

        if link.security == "reality" || link.security == "tls" {
            var tls: [String: Any] = [
                "enabled": true,
                "server_name": link.sni ?? link.host,
                "utls": ["enabled": true, "fingerprint": link.fingerprint ?? "chrome"],
            ]
            if link.security == "reality" {
                tls["reality"] = ["enabled": true, "public_key": link.publicKey ?? "", "short_id": link.shortId ?? ""]
            }
            outbound["tls"] = tls
        }

        switch link.network {
        case "grpc":
            outbound["transport"] = ["type": "grpc", "service_name": link.serviceName ?? ""]
        case "ws":
            var transport: [String: Any] = ["type": "ws", "path": link.path ?? "/"]
            if let host = link.hostHeader, !host.isEmpty { transport["headers"] = ["Host": host] }
            outbound["transport"] = transport
        case "httpupgrade":
            var transport: [String: Any] = ["type": "httpupgrade", "path": link.path ?? "/"]
            if let host = link.hostHeader, !host.isEmpty { transport["host"] = host }
            outbound["transport"] = transport
        default:
            break
        }
        return outbound
    }
}

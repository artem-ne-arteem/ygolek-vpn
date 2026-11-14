import Foundation
import UIKit

/// Сервер из подписки: vless://uuid@host:port?параметры#название
/// (тот же формат и разбор, что в Windows-клиенте — windows/YgolekVpn/Services/VlessLink.cs)
struct VlessLink: Identifiable, Hashable {
    let name: String
    let uuid: String
    let host: String
    let port: Int
    let network: String
    let security: String
    let sni: String?
    let fingerprint: String?
    let publicKey: String?
    let shortId: String?
    let flow: String?
    let serviceName: String?
    let path: String?
    let hostHeader: String?

    var id: String { name + host + String(port) }

    /// Панель отдаёт «client1 · 🇳🇱⭐️Нидерланды» — показываем часть после « · » без эмодзи
    var displayName: String {
        let tail = name.components(separatedBy: " · ").last ?? name
        let clean = tail.unicodeScalars.filter {
            CharacterSet.letters.contains($0) || CharacterSet.decimalDigits.contains($0)
                || $0 == " " || $0 == "-" || $0 == "." || $0 == "(" || $0 == ")"
        }
        let text = String(String.UnicodeScalarView(clean)).trimmingCharacters(in: .whitespaces)
        return text.isEmpty ? host : text
    }

    init?(_ line: String) {
        let line = line.trimmingCharacters(in: .whitespacesAndNewlines)
        guard line.lowercased().hasPrefix("vless://"),
              let components = URLComponents(string: line),
              let host = components.host,
              let user = components.user
        else { return nil }

        let query = Dictionary(
            (components.queryItems ?? []).map { ($0.name, $0.value ?? "") },
            uniquingKeysWith: { first, _ in first }
        )
        let fragment = components.fragment ?? ""
        name = fragment.isEmpty ? host : fragment
        uuid = user.removingPercentEncoding ?? user
        self.host = host
        port = components.port ?? 443
        network = query["type"] ?? "tcp"
        security = query["security"] ?? "none"
        sni = query["sni"]
        fingerprint = query["fp"]
        publicKey = query["pbk"]
        shortId = query["sid"]
        flow = query["flow"]
        serviceName = query["serviceName"]
        path = query["path"]
        hostHeader = query["host"]
    }
}

enum SubscriptionError: Error {
    /// На подписке уже подключено максимум устройств — новое панель не пускает
    case deviceLimit
    case http(Int)
}

enum SubscriptionLoader {
    /// Скачивает подписку (base64 или текст со ссылками) и возвращает серверы.
    static func load(_ urlString: String) async throws -> [VlessLink] {
        guard let url = URL(string: urlString) else { return [] }
        var request = URLRequest(url: url)
        let version = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "0"
        request.setValue("YgolekVPN-iOS/\(version)", forHTTPHeaderField: "User-Agent")
        // по этим заголовкам панель учитывает устройство в лимите подписки
        request.setValue(Storage.deviceId, forHTTPHeaderField: "x-hwid")
        request.setValue("iOS", forHTTPHeaderField: "x-device-os")
        request.setValue(UIDevice.current.model, forHTTPHeaderField: "x-device-model")

        let (data, response) = try await URLSession.shared.data(for: request)
        let body = (String(data: data, encoding: .utf8) ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        let status = (response as? HTTPURLResponse)?.statusCode ?? 0
        guard (200 ..< 300).contains(status) else {
            // панель отвечает {"ok":false,"error":"device_limit_exceeded",...}
            if body.contains("device_limit_exceeded") { throw SubscriptionError.deviceLimit }
            throw SubscriptionError.http(status)
        }
        let text = body.contains("://") ? body : decodeBase64(body)
        return text.split(whereSeparator: \.isNewline).compactMap { VlessLink(String($0)) }
    }

    private static func decodeBase64(_ value: String) -> String {
        var s = value.replacingOccurrences(of: "-", with: "+").replacingOccurrences(of: "_", with: "/")
            .components(separatedBy: .whitespacesAndNewlines).joined()
        s += String(repeating: "=", count: (4 - s.count % 4) % 4)
        guard let data = Data(base64Encoded: s) else { return "" }
        return String(data: data, encoding: .utf8) ?? ""
    }
}

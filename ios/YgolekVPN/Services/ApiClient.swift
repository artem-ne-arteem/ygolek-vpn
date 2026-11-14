import Foundation

/// API сайта для приложения (site/app/api/app/*): вход через бота и данные аккаунта.
struct ApiClient {
    static let baseURL = URL(string: "https://ygolek-vpn.online")!

    struct LoginStart: Decodable {
        let code: String
        let secret: String
        let botUrl: String
        let expiresIn: Int
    }

    struct LoginPoll: Decodable {
        let status: String
        let token: String?
    }

    struct Account: Decodable {
        struct Subscription: Decodable {
            let planId: String
            let expiresAt: Date
        }

        let tgId: Int64
        let username: String?
        let deviceLimit: Int
        let subscription: Subscription?
        let key: String?
        let renewUrl: String
        let botUrl: String
    }

    enum ApiError: Error {
        case unauthorized
        case http(Int)
    }

    private let session: URLSession = {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 20
        return URLSession(configuration: config)
    }()

    private static let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .custom { decoder in
            let value = try decoder.singleValueContainer().decode(String.self)
            let formatter = ISO8601DateFormatter()
            formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
            if let date = formatter.date(from: value) { return date }
            formatter.formatOptions = [.withInternetDateTime]
            if let date = formatter.date(from: value) { return date }
            throw DecodingError.dataCorrupted(.init(codingPath: decoder.codingPath, debugDescription: "bad date \(value)"))
        }
        return decoder
    }()

    func startLogin(device: String) async throws -> LoginStart {
        try await post("/api/app/login/start", body: ["device": device])
    }

    func pollLogin(code: String, secret: String) async throws -> LoginPoll {
        do {
            return try await post("/api/app/login/poll", body: ["code": code, "secret": secret])
        } catch ApiError.http(let status) where status == 400 || status == 404 {
            return LoginPoll(status: "invalid", token: nil)
        }
    }

    /// nil — токен больше не действует (вышли из аккаунта и т.п.)
    func account(token: String) async throws -> Account? {
        var request = URLRequest(url: Self.baseURL.appendingPathComponent("/api/app/me"))
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        do {
            return try await send(request)
        } catch ApiError.unauthorized {
            return nil
        }
    }

    func logout(token: String) async {
        var request = URLRequest(url: Self.baseURL.appendingPathComponent("/api/app/logout"))
        request.httpMethod = "POST"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        _ = try? await session.data(for: request)
    }

    private func post<T: Decodable>(_ path: String, body: [String: String]) async throws -> T {
        var request = URLRequest(url: Self.baseURL.appendingPathComponent(path))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        return try await send(request)
    }

    private func send<T: Decodable>(_ request: URLRequest) async throws -> T {
        let (data, response) = try await session.data(for: request)
        let status = (response as? HTTPURLResponse)?.statusCode ?? 0
        if status == 401 { throw ApiError.unauthorized }
        guard (200 ..< 300).contains(status) else { throw ApiError.http(status) }
        return try Self.decoder.decode(T.self, from: data)
    }
}

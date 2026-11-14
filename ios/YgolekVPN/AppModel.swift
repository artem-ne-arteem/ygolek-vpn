import Foundation
import UIKit

/// Состояние приложения: вход через бота, аккаунт, серверы.
@MainActor
final class AppModel: ObservableObject {
    enum Screen { case loading, login, home }

    @Published var screen: Screen = .loading
    @Published var account: ApiClient.Account?
    @Published var servers: [VlessLink] = []
    @Published var selectedServer: VlessLink? {
        didSet { Storage.lastServer = selectedServer?.name }
    }
    @Published var message: String?

    // Вход
    @Published var loginBotURL: URL?
    @Published var loginStatus = ""
    @Published var loginFailed = false

    private let api = ApiClient()
    private var loginTask: Task<Void, Never>?

    func start() async {
        if Storage.token == nil {
            startLogin()
        } else {
            await loadAccount()
        }
    }

    // MARK: Вход через бота

    func startLogin() {
        screen = .login
        loginTask?.cancel()
        loginFailed = false
        loginBotURL = nil
        loginStatus = "Готовим ссылку…"
        loginTask = Task { await runLogin() }
    }

    private func runLogin() async {
        let start: ApiClient.LoginStart
        do {
            start = try await api.startLogin(device: "iPhone · \(UIDevice.current.name)")
        } catch {
            loginStatus = "Нет связи с сервером. Проверь интернет."
            loginFailed = true
            return
        }
        loginBotURL = URL(string: start.botUrl)
        loginStatus = "Ждём подтверждения в боте…"

        let deadline = Date().addingTimeInterval(TimeInterval(start.expiresIn))
        while !Task.isCancelled, Date() < deadline {
            try? await Task.sleep(nanoseconds: 2_000_000_000)
            guard !Task.isCancelled,
                  let poll = try? await api.pollLogin(code: start.code, secret: start.secret)
            else { continue }

            switch poll.status {
            case "ok":
                if let token = poll.token {
                    Storage.token = token
                    await loadAccount()
                    return
                }
            case "denied":
                loginStatus = "Вход отменён в боте."
                loginFailed = true
                return
            case "expired", "invalid":
                loginStatus = "Ссылка устарела."
                loginFailed = true
                return
            default:
                break
            }
        }
        if !Task.isCancelled {
            loginStatus = "Ссылка устарела."
            loginFailed = true
        }
    }

    // MARK: Аккаунт и серверы

    func loadAccount() async {
        guard let token = Storage.token else { return startLogin() }
        if screen != .home { screen = .loading }
        message = nil

        let account: ApiClient.Account?
        do {
            account = try await api.account(token: token)
        } catch {
            screen = .home
            message = "Нет связи с сервером. Потяни экран вниз, чтобы обновить."
            return
        }
        guard let account else {
            // токен отозван — входим заново
            Storage.token = nil
            return startLogin()
        }
        self.account = account
        screen = .home

        guard account.subscription != nil, let key = account.key else {
            servers = []
            selectedServer = nil
            return
        }
        do {
            let servers = try await SubscriptionLoader.load(key)
            self.servers = servers
            selectedServer = servers.first { $0.name == Storage.lastServer } ?? servers.first
            if servers.isEmpty { message = "В подписке нет серверов. Напиши в поддержку." }
        } catch {
            message = "Не удалось загрузить список серверов. Проверь интернет."
        }
    }

    func logout() async {
        if let token = Storage.token { await api.logout(token: token) }
        Storage.token = nil
        account = nil
        servers = []
        selectedServer = nil
        startLogin()
    }
}

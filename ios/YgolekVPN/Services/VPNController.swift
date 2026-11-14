import Foundation
import NetworkExtension

/// Профиль VPN в настройках iOS и запуск/остановка VPN-модуля.
@MainActor
final class VPNController: ObservableObject {
    @Published private(set) var status: NEVPNStatus = .invalid
    @Published private(set) var connectedSince: Date?
    @Published var lastError: String?

    private var manager: NETunnelProviderManager?
    private var observer: NSObjectProtocol?

    init() {
        observer = NotificationCenter.default.addObserver(
            forName: .NEVPNStatusDidChange, object: nil, queue: .main
        ) { [weak self] _ in
            Task { @MainActor in self?.refreshStatus() }
        }
        Task { await load() }
    }

    var isActive: Bool { status == .connected || status == .connecting || status == .reasserting }

    func load() async {
        let managers = (try? await NETunnelProviderManager.loadAllFromPreferences()) ?? []
        manager = managers.first
        refreshStatus()
    }

    func connect(config: String) async {
        lastError = nil
        do {
            let manager = try await prepareManager()
            try manager.connection.startVPNTunnel(options: ["configContent": config as NSString])
        } catch {
            lastError = "Не удалось включить VPN: \(error.localizedDescription)"
        }
    }

    func disconnect() {
        manager?.connection.stopVPNTunnel()
    }

    /// Создаёт (или обновляет) профиль «Ygolek VPN» в настройках iOS.
    /// В первый раз iOS спросит разрешение на добавление конфигурации VPN.
    private func prepareManager() async throws -> NETunnelProviderManager {
        let manager = manager ?? NETunnelProviderManager()
        let proto = (manager.protocolConfiguration as? NETunnelProviderProtocol) ?? NETunnelProviderProtocol()
        proto.providerBundleIdentifier = Self.tunnelBundleIdentifier
        proto.serverAddress = "Ygolek VPN"
        manager.protocolConfiguration = proto
        manager.localizedDescription = "Ygolek VPN"
        manager.isEnabled = true
        try await manager.saveToPreferences()
        // после сохранения профиль нужно перечитать, иначе первый запуск падает
        try await manager.loadFromPreferences()
        self.manager = manager
        return manager
    }

    /// Идентификатор VPN-модуля берём из самого .appex: программы подписи
    /// (ESign, Feather) могут переименовать bundle id при установке.
    private static var tunnelBundleIdentifier: String {
        if let plugins = Bundle.main.builtInPlugInsURL,
           let items = try? FileManager.default.contentsOfDirectory(at: plugins, includingPropertiesForKeys: nil),
           let appex = items.first(where: { $0.pathExtension == "appex" }),
           let id = Bundle(url: appex)?.bundleIdentifier
        {
            return id
        }
        return (Bundle.main.bundleIdentifier ?? "app.vanilla7419.emerald5335") + ".tunnel"
    }

    private func refreshStatus() {
        let newStatus = manager?.connection.status ?? .invalid
        if newStatus == .connected {
            connectedSince = manager?.connection.connectedDate ?? connectedSince ?? Date()
        } else if newStatus != .reasserting {
            connectedSince = nil
        }
        // VPN-модуль упал при запуске или во время работы — покажем почему
        if newStatus == .disconnected, status == .connecting || status == .connected {
            fetchDisconnectError()
        }
        status = newStatus
    }

    private func fetchDisconnectError() {
        guard #available(iOS 16.0, *), let connection = manager?.connection else { return }
        connection.fetchLastDisconnectError { [weak self] error in
            guard let error else { return }
            Task { @MainActor in
                self?.lastError = error.localizedDescription
            }
        }
    }
}

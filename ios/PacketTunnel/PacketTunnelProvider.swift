import Foundation
import Libbox
import NetworkExtension
import os.log

/// VPN-модуль: получает от приложения готовый конфиг sing-box и запускает ядро.
/// Упрощённая версия ExtensionProvider из sing-box-for-apple (GPL-3.0).
final class PacketTunnelProvider: NEPacketTunnelProvider {
    static let logger = Logger(subsystem: "app.vanilla7419.emerald5335.tunnel", category: "tunnel")

    private var commandServer: LibboxCommandServer?
    private lazy var platformInterface = PlatformInterface(self)

    private static var directory: URL {
        let url = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("sing-box", isDirectory: true)
        try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        return url
    }

    /// Последний конфиг — если iOS перезапустит VPN сама (без приложения)
    private static var configCacheURL: URL { directory.appendingPathComponent("config.json") }

    override func startTunnel(options: [String: NSObject]?) async throws {
        let config: String
        if let content = options?["configContent"] as? String {
            config = content
            try? content.write(to: Self.configCacheURL, atomically: true, encoding: .utf8)
        } else if let cached = try? String(contentsOf: Self.configCacheURL, encoding: .utf8) {
            config = cached
        } else {
            throw tunnelError("Нет настроек подключения — открой приложение и подключись заново")
        }

        let setup = LibboxSetupOptions()
        setup.basePath = Self.directory.path
        setup.workingPath = Self.directory.appendingPathComponent("working").path
        setup.tempPath = FileManager.default.temporaryDirectory.path
        setup.logMaxLines = 300
        // в расширении жёсткий лимит памяти (~50 МБ) — пусть ядро следит за ним само
        setup.oomKillerEnabled = true
        try? FileManager.default.createDirectory(atPath: setup.workingPath, withIntermediateDirectories: true)

        var setupError: NSError?
        LibboxSetup(setup, &setupError)
        if let setupError {
            throw tunnelError("Не удалось подготовить ядро: \(setupError.localizedDescription)")
        }

        var error: NSError?
        commandServer = LibboxNewCommandServer(platformInterface, platformInterface, &error)
        if let error {
            throw tunnelError("Не удалось запустить ядро: \(error.localizedDescription)")
        }
        do {
            try commandServer!.startOrReloadService(config, options: LibboxOverrideOptions())
        } catch {
            Self.logger.error("start service: \(error.localizedDescription, privacy: .public)")
            throw tunnelError("Не удалось подключиться: \(error.localizedDescription)")
        }
        Self.logger.info("tunnel started")
    }

    override func stopTunnel(with reason: NEProviderStopReason) async {
        Self.logger.info("stopping, reason: \(reason.rawValue)")
        stopService()
        commandServer?.close()
        commandServer = nil
    }

    func stopService() {
        try? commandServer?.closeService()
        platformInterface.reset()
    }

    func reloadService() async throws {
        guard let config = try? String(contentsOf: Self.configCacheURL, encoding: .utf8) else { return }
        reasserting = true
        defer { reasserting = false }
        try commandServer?.startOrReloadService(config, options: LibboxOverrideOptions())
    }

    func writeMessage(_ message: String) {
        Self.logger.info("\(message, privacy: .public)")
    }

    override func sleep() async {
        commandServer?.pause()
    }

    override func wake() {
        commandServer?.wake()
    }

    private func tunnelError(_ message: String) -> NSError {
        NSError(domain: "YgolekVPN", code: 1, userInfo: [NSLocalizedDescriptionKey: message])
    }
}

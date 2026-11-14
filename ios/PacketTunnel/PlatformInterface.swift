// Связка ядра sing-box с NetworkExtension на iOS.
// Основано на ExtensionPlatformInterface.swift из sing-box-for-apple 1.14.4
// (https://github.com/SagerNet/sing-box-for-apple, GPL-3.0) — оставлена только
// часть для iOS, без macOS / tvOS / jailbreak.

import Foundation
import Libbox
import Network
import NetworkExtension

final class PlatformInterface: NSObject, LibboxPlatformInterfaceProtocol, LibboxCommandServerHandlerProtocol {
    private unowned let tunnel: PacketTunnelProvider
    private var networkSettings: NEPacketTunnelNetworkSettings?
    private var nwMonitor: NWPathMonitor?
    private var lastNetworkPath: String?

    init(_ tunnel: PacketTunnelProvider) {
        self.tunnel = tunnel
    }

    func reset() {
        networkSettings = nil
        nwMonitor?.cancel()
        nwMonitor = nil
        lastNetworkPath = nil
    }

    // MARK: TUN

    func openTun(_ options: LibboxTunOptionsProtocol?, ret0_: UnsafeMutablePointer<Int32>?) throws {
        try runBlocking { [self] in
            try await openTun0(options, ret0_)
        }
    }

    private func openTun0(_ options: LibboxTunOptionsProtocol?, _ ret0_: UnsafeMutablePointer<Int32>?) async throws {
        guard let options, let ret0_ else {
            throw platformError("openTun: missing options")
        }

        let settings = NEPacketTunnelNetworkSettings(tunnelRemoteAddress: "127.0.0.1")
        if options.getAutoRoute() {
            settings.mtu = NSNumber(value: options.getMTU())

            var dnsSettings: NEDNSSettings?
            if options.getDNSMode()!.value != LibboxDNSModeDisabled {
                let dnsServerIterator = try options.getDNSServerAddress()
                var dnsServers: [String] = []
                while dnsServerIterator.hasNext() {
                    dnsServers.append(dnsServerIterator.next())
                }
                if !dnsServers.isEmpty {
                    dnsSettings = NEDNSSettings(servers: dnsServers)
                }
            }

            var ipv4Address: [String] = []
            var ipv4Mask: [String] = []
            let ipv4AddressIterator = options.getInet4Address()!
            while ipv4AddressIterator.hasNext() {
                let prefix = ipv4AddressIterator.next()!
                ipv4Address.append(prefix.address())
                ipv4Mask.append(prefix.mask())
            }
            let ipv4Settings = NEIPv4Settings(addresses: ipv4Address, subnetMasks: ipv4Mask)
            var ipv4Routes: [NEIPv4Route] = []
            var ipv4ExcludeRoutes: [NEIPv4Route] = []
            let inet4RouteIterator = options.getInet4RouteAddress()!
            if inet4RouteIterator.hasNext() {
                while inet4RouteIterator.hasNext() {
                    let prefix = inet4RouteIterator.next()!
                    ipv4Routes.append(NEIPv4Route(destinationAddress: prefix.address(), subnetMask: prefix.mask()))
                }
            } else {
                ipv4Routes.append(NEIPv4Route.default())
            }
            let inet4ExcludeIterator = options.getInet4RouteExcludeAddress()!
            while inet4ExcludeIterator.hasNext() {
                let prefix = inet4ExcludeIterator.next()!
                ipv4ExcludeRoutes.append(NEIPv4Route(destinationAddress: prefix.address(), subnetMask: prefix.mask()))
            }
            ipv4Settings.includedRoutes = ipv4Routes
            ipv4Settings.excludedRoutes = ipv4ExcludeRoutes
            settings.ipv4Settings = ipv4Settings

            var ipv6Address: [String] = []
            var ipv6Prefixes: [NSNumber] = []
            let ipv6AddressIterator = options.getInet6Address()!
            while ipv6AddressIterator.hasNext() {
                let prefix = ipv6AddressIterator.next()!
                ipv6Address.append(prefix.address())
                ipv6Prefixes.append(NSNumber(value: prefix.prefix()))
            }
            let ipv6Settings = NEIPv6Settings(addresses: ipv6Address, networkPrefixLengths: ipv6Prefixes)
            var ipv6Routes: [NEIPv6Route] = []
            var ipv6ExcludeRoutes: [NEIPv6Route] = []
            let inet6RouteIterator = options.getInet6RouteAddress()!
            if inet6RouteIterator.hasNext() {
                while inet6RouteIterator.hasNext() {
                    let prefix = inet6RouteIterator.next()!
                    ipv6Routes.append(NEIPv6Route(destinationAddress: prefix.address(), networkPrefixLength: NSNumber(value: prefix.prefix())))
                }
            } else {
                ipv6Routes.append(NEIPv6Route.default())
            }
            let inet6ExcludeIterator = options.getInet6RouteExcludeAddress()!
            while inet6ExcludeIterator.hasNext() {
                let prefix = inet6ExcludeIterator.next()!
                ipv6ExcludeRoutes.append(NEIPv6Route(destinationAddress: prefix.address(), networkPrefixLength: NSNumber(value: prefix.prefix())))
            }
            ipv6Settings.includedRoutes = ipv6Routes
            ipv6Settings.excludedRoutes = ipv6ExcludeRoutes
            settings.ipv6Settings = ipv6Settings

            let hasDefaultRoute = ipv4Routes.contains {
                $0.destinationAddress == "0.0.0.0" && $0.destinationSubnetMask == "0.0.0.0"
            }
            if !hasDefaultRoute {
                dnsSettings?.matchDomains = [""]
                dnsSettings?.matchDomainsNoSearch = true
            }
            settings.dnsSettings = dnsSettings
        }

        if options.isHTTPProxyEnabled() {
            let proxySettings = NEProxySettings()
            let proxyServer = NEProxyServer(address: options.getHTTPProxyServer(), port: Int(options.getHTTPProxyServerPort()))
            proxySettings.httpServer = proxyServer
            proxySettings.httpsServer = proxyServer
            proxySettings.httpEnabled = true
            proxySettings.httpsEnabled = true
            settings.proxySettings = proxySettings
        }

        networkSettings = settings
        try await tunnel.setTunnelNetworkSettings(settings)

        if let tunFd = tunnel.packetFlow.value(forKeyPath: "socket.fileDescriptor") as? Int32 {
            ret0_.pointee = tunFd
            return
        }
        let tunFdFromLoop = LibboxGetTunnelFileDescriptor()
        if tunFdFromLoop != -1 {
            ret0_.pointee = tunFdFromLoop
        } else {
            throw platformError("Missing tunnel file descriptor")
        }
    }

    // MARK: Сеть

    func usePlatformAutoDetectControl() -> Bool { false }

    func autoDetectControl(_: Int32) throws {}

    func startDefaultInterfaceMonitor(_ listener: LibboxInterfaceUpdateListenerProtocol?) throws {
        guard let listener else { return }
        let monitor = NWPathMonitor()
        nwMonitor = monitor
        let semaphore = DispatchSemaphore(value: 0)
        monitor.pathUpdateHandler = { path in
            self.onUpdateDefaultInterface(listener, path)
            semaphore.signal()
            monitor.pathUpdateHandler = { path in
                self.onUpdateDefaultInterface(listener, path)
            }
        }
        monitor.start(queue: DispatchQueue.global())
        semaphore.wait()
    }

    private func onUpdateDefaultInterface(_ listener: LibboxInterfaceUpdateListenerProtocol, _ path: Network.NWPath) {
        let networkPath = "\(path.status) \(path.availableInterfaces.map { "\($0.name)#\($0.index)" }.joined(separator: ","))"
        listener.updateNetworkPath(networkPath)
        if networkPath == lastNetworkPath { return }
        lastNetworkPath = networkPath
        guard path.status != .unsatisfied, let defaultInterface = path.availableInterfaces.first else {
            listener.updateDefaultInterface("", interfaceIndex: -1, isExpensive: false, isConstrained: false)
            return
        }
        listener.updateDefaultInterface(defaultInterface.name, interfaceIndex: Int32(defaultInterface.index),
                                        isExpensive: path.isExpensive, isConstrained: path.isConstrained)
    }

    func closeDefaultInterfaceMonitor(_: LibboxInterfaceUpdateListenerProtocol?) throws {
        nwMonitor?.cancel()
        nwMonitor = nil
        lastNetworkPath = nil
    }

    func getInterfaces() throws -> LibboxNetworkInterfaceIteratorProtocol {
        guard let nwMonitor else {
            throw platformError("NWMonitor not started")
        }
        let path = nwMonitor.currentPath
        if path.status == .unsatisfied {
            return NetworkInterfaceArray([])
        }
        var interfaces: [LibboxNetworkInterface] = []
        for it in path.availableInterfaces {
            let interface = LibboxNetworkInterface()
            interface.name = it.name
            interface.index = Int32(it.index)
            switch it.type {
            case .wifi: interface.type = LibboxInterfaceTypeWIFI
            case .cellular: interface.type = LibboxInterfaceTypeCellular
            case .wiredEthernet: interface.type = LibboxInterfaceTypeEthernet
            default: interface.type = LibboxInterfaceTypeOther
            }
            interfaces.append(interface)
        }
        return NetworkInterfaceArray(interfaces)
    }

    private final class NetworkInterfaceArray: NSObject, LibboxNetworkInterfaceIteratorProtocol {
        private var iterator: IndexingIterator<[LibboxNetworkInterface]>
        private var nextValue: LibboxNetworkInterface?

        init(_ array: [LibboxNetworkInterface]) {
            iterator = array.makeIterator()
        }

        func hasNext() -> Bool {
            nextValue = iterator.next()
            return nextValue != nil
        }

        func next() -> LibboxNetworkInterface? { nextValue }
    }

    func underNetworkExtension() -> Bool { true }

    func includeAllNetworks() -> Bool { false }

    func clearDNSCache() {
        guard let networkSettings else { return }
        runBlocking {
            self.tunnel.reasserting = true
            defer { self.tunnel.reasserting = false }
            await withCheckedContinuation { continuation in
                self.tunnel.setTunnelNetworkSettings(nil) { _ in continuation.resume() }
            }
            await withCheckedContinuation { continuation in
                self.tunnel.setTunnelNetworkSettings(networkSettings) { _ in continuation.resume() }
            }
        }
    }

    func readWIFIState() -> LibboxWIFIState? { nil }

    func readWIFISSID() -> String? { nil }

    func localDNSTransport() -> (any LibboxLocalDNSTransportProtocol)? { nil }

    func systemCertificates() -> (any LibboxStringIteratorProtocol)? { nil }

    func findConnectionOwner(_: Int32, sourceAddress _: String?, sourcePort _: Int32, destinationAddress _: String?, destinationPort _: Int32) throws -> LibboxConnectionOwner {
        throw platformError("Not implemented")
    }

    func startNeighborMonitor(_: LibboxNeighborUpdateListenerProtocol?) throws {}

    func closeNeighborMonitor(_: LibboxNeighborUpdateListenerProtocol?) throws {}

    func registerMyInterface(_: String?) {}

    // MARK: Логи и уведомления

    func writeLog(_ message: String?) {
        guard let message else { return }
        tunnel.writeMessage(message)
    }

    func writeDebugMessage(_ message: String?) {
        guard let message else { return }
        tunnel.writeMessage(message)
    }

    func send(_: LibboxNotification?) throws {}

    func cancelNotification(_: String?, typeID _: Int32) throws {}

    // MARK: Управление сервисом

    func serviceStop() throws {
        tunnel.stopService()
    }

    func serviceReload() throws {
        try runBlocking { [self] in
            try await tunnel.reloadService()
        }
    }

    func getSystemProxyStatus() throws -> LibboxSystemProxyStatus {
        let status = LibboxSystemProxyStatus()
        guard let proxySettings = networkSettings?.proxySettings, proxySettings.httpServer != nil else {
            return status
        }
        status.available = true
        status.enabled = proxySettings.httpEnabled
        return status
    }

    func setSystemProxyEnabled(_: Bool) throws {}

    func triggerNativeCrash() throws {}

    func connectSSHAgent(_: UnsafeMutablePointer<Int32>?) throws {
        throw platformError("SSH agent forwarding is not supported")
    }

    // MARK: Не используется на iOS (SSH, Tailscale, мосты)

    func usePlatformShell() -> Bool { false }

    func checkPlatformShell() throws {
        throw platformError("Not supported")
    }

    func openShellSession(_: LibboxPlatformUser?, command _: String?, environ _: (any LibboxStringIteratorProtocol)?, term _: String?, rows _: Int32, cols _: Int32) throws -> any LibboxShellSessionProtocol {
        throw platformError("Not supported")
    }

    func readSystemSSHHostKey(_ error: NSErrorPointer) -> String {
        error?.pointee = platformError("Not supported")
        return ""
    }

    func lookupSFTPServer(_ error: NSErrorPointer) -> String {
        error?.pointee = platformError("Not supported")
        return ""
    }

    func lookupUser(_: String?) throws -> LibboxPlatformUser {
        throw platformError("Not supported")
    }

    func tailscaleHostname() -> String { "" }

    func usePlatformBridge() -> Bool { false }

    func createBridge(_: LibboxBridgeOptions?) throws -> any LibboxBridgeSessionProtocol {
        throw platformError("Not supported")
    }

    private func platformError(_ message: String) -> NSError {
        NSError(domain: "PlatformInterface", code: 0, userInfo: [NSLocalizedDescriptionKey: message])
    }
}

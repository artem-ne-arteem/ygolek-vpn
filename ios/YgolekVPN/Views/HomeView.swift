import NetworkExtension
import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var model: AppModel
    @EnvironmentObject private var vpn: VPNController

    var body: some View {
        ScrollView {
            VStack(spacing: 14) {
                HStack {
                    Header()
                    StatusPill(status: vpn.status)
                }

                PowerSection()
                    .padding(.vertical, 14)

                if let error = vpn.lastError ?? model.message {
                    HStack(alignment: .top, spacing: 10) {
                        Image(systemName: "exclamationmark.circle.fill")
                            .foregroundStyle(Theme.danger)
                        Text(error)
                            .font(.footnote)
                            .foregroundStyle(Theme.primary)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                    .padding(14)
                    .glassCard(cornerRadius: 20)
                }

                ServersCard()
                SubscriptionCard()

                HStack {
                    Link(destination: Theme.supportURL) {
                        Label("Поддержка", systemImage: "bubble.left")
                    }
                    Spacer()
                    Button {
                        vpn.disconnect()
                        Task { await model.logout() }
                    } label: {
                        Text(model.account?.username.map { "@\($0) · Выйти" } ?? "Выйти")
                    }
                }
                .font(.footnote)
                .foregroundStyle(Theme.tertiary)
                .padding(.horizontal, 6)
                .padding(.top, 4)
            }
            .padding(20)
        }
        .scrollIndicators(.hidden)
        .refreshable { await model.loadAccount() }
    }
}

private struct StatusPill: View {
    let status: NEVPNStatus

    var body: some View {
        let on = status == .connected
        let text = switch status {
        case .connected: "Защищено"
        case .connecting, .reasserting: "Подключение"
        case .disconnecting: "Отключение"
        default: "Отключено"
        }
        HStack(spacing: 6) {
            Circle()
                .fill(on ? Theme.primary : Theme.tertiary)
                .frame(width: 6, height: 6)
            Text(text)
                .font(.caption.weight(.medium))
                .foregroundStyle(on ? Theme.primary : Theme.secondary)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 7)
        .glass(in: Capsule())
    }
}

private struct PowerSection: View {
    @EnvironmentObject private var model: AppModel
    @EnvironmentObject private var vpn: VPNController
    @State private var pulse = false

    private var connected: Bool { vpn.status == .connected }
    private var busy: Bool { vpn.status == .connecting || vpn.status == .disconnecting || vpn.status == .reasserting }

    var body: some View {
        VStack(spacing: 12) {
            Button(action: toggle) {
                ZStack {
                    if connected {
                        // включено — сплошной белый круг со свечением
                        Circle()
                            .fill(.white)
                            .shadow(color: .white.opacity(0.45), radius: 40)
                    } else {
                        Circle()
                            .fill(.clear)
                            .glass(in: Circle(), interactive: true)
                        Circle()
                            .stroke(Theme.primary.opacity(busy ? (pulse ? 0.15 : 0.7) : 0.25), lineWidth: 2)
                            .padding(10)
                    }
                    Image(systemName: "power")
                        .font(.system(size: 50, weight: .light))
                        .foregroundStyle(connected ? .black : .white)
                }
                .frame(width: 170, height: 170)
                .contentShape(Circle())
            }
            .buttonStyle(.plain)
            .disabled(busy || (!vpn.isActive && model.selectedServer == nil))
            .animation(.easeInOut(duration: 0.8).repeatForever(), value: pulse)
            .animation(.spring(response: 0.4, dampingFraction: 0.8), value: connected)
            .onAppear { pulse = true }

            Text(title)
                .font(.system(size: 28, weight: .bold))
                .padding(.top, 8)
            TimelineView(.periodic(from: .now, by: 1)) { context in
                Text(subtitle(now: context.date))
                    .font(.subheadline)
                    .foregroundStyle(Theme.secondary)
                    .monospacedDigit()
            }
        }
        .frame(maxWidth: .infinity)
    }

    private var title: String {
        switch vpn.status {
        case .connected: "Подключено"
        case .connecting, .reasserting: "Подключение…"
        case .disconnecting: "Отключение…"
        default: "Не подключено"
        }
    }

    private func subtitle(now: Date) -> String {
        let server = model.selectedServer?.displayName ?? ""
        if vpn.status == .connected, let since = vpn.connectedSince {
            let s = max(0, Int(now.timeIntervalSince(since)))
            return String(format: "%@ · %02d:%02d:%02d", server, s / 3600, s / 60 % 60, s % 60)
        }
        if vpn.isActive { return server }
        if model.account?.subscription == nil { return "Нужна активная подписка" }
        return model.servers.isEmpty ? "Нет доступных серверов" : "Нажми, чтобы подключиться"
    }

    private func toggle() {
        if vpn.isActive {
            vpn.disconnect()
            return
        }
        guard let server = model.selectedServer else { return }
        do {
            let config = try SingBoxConfig.build(server)
            Task { await vpn.connect(config: config) }
        } catch {
            vpn.lastError = "Не удалось собрать настройки подключения"
        }
    }
}

private struct ServersCard: View {
    @EnvironmentObject private var model: AppModel
    @EnvironmentObject private var vpn: VPNController

    var body: some View {
        Card {
            SectionLabel(text: "СЕРВЕРЫ")
                .padding(.bottom, 12)
            if model.servers.isEmpty {
                Text(model.account?.subscription == nil ? "Серверы появятся после оформления подписки." : "Список пуст")
                    .font(.subheadline)
                    .foregroundStyle(Theme.secondary)
            }
            VStack(spacing: 8) {
                ForEach(model.servers) { server in
                    let selected = server == model.selectedServer
                    Button {
                        model.selectedServer = server
                    } label: {
                        HStack(spacing: 12) {
                            Image(systemName: "globe")
                                .foregroundStyle(selected ? Theme.primary : Theme.tertiary)
                            Text(server.displayName)
                                .foregroundStyle(Theme.primary)
                            Spacer()
                            Image(systemName: selected ? "checkmark.circle.fill" : "circle")
                                .foregroundStyle(selected ? Theme.primary : Theme.tertiary)
                        }
                        .padding(.horizontal, 16)
                        .padding(.vertical, 14)
                        .background(selected ? Color.white.opacity(0.12) : Theme.fill,
                                    in: RoundedRectangle(cornerRadius: 16, style: .continuous))
                        .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous)
                            .stroke(selected ? Color.white.opacity(0.5) : Theme.stroke))
                    }
                    .buttonStyle(.plain)
                    .disabled(vpn.isActive)
                    .opacity(vpn.isActive && !selected ? 0.45 : 1)
                }
            }
        }
    }
}

private struct SubscriptionCard: View {
    @EnvironmentObject private var model: AppModel
    @Environment(\.openURL) private var openURL

    var body: some View {
        Card {
            HStack(alignment: .center) {
                VStack(alignment: .leading, spacing: 5) {
                    SectionLabel(text: "ПОДПИСКА")
                    Text(title).font(.system(size: 19, weight: .semibold))
                    Text(details).font(.footnote).foregroundStyle(Theme.secondary)
                }
                Spacer()
                Button(model.account?.subscription == nil ? "Оформить" : "Продлить") {
                    guard let account = model.account else { return }
                    let url = account.subscription == nil ? account.botUrl : account.renewUrl
                    if let url = URL(string: url) { openURL(url) }
                }
                .buttonStyle(GlassButtonStyle())
            }
            if model.account?.subscription != nil {
                GeometryReader { geo in
                    ZStack(alignment: .leading) {
                        Capsule().fill(Theme.fill)
                        Capsule()
                            .fill(daysLeft <= 3 ? Theme.danger : Theme.primary)
                            .frame(width: geo.size.width * CGFloat(min(daysLeft, 30)) / 30)
                    }
                }
                .frame(height: 5)
                .padding(.top, 16)
            }
        }
    }

    private var daysLeft: Int {
        guard let expires = model.account?.subscription?.expiresAt else { return 0 }
        return max(0, Int((expires.timeIntervalSinceNow / 86400).rounded(.up)))
    }

    private var title: String {
        guard let expires = model.account?.subscription?.expiresAt else { return "Нет активной подписки" }
        return "До \(expires.formatted(.dateTime.day(.twoDigits).month(.twoDigits).year()))"
    }

    private var details: String {
        guard let account = model.account else { return "" }
        if account.subscription == nil { return "Оформи в боте и потяни экран вниз" }
        return "Осталось \(daysLabel(daysLeft)) · до \(account.deviceLimit) устройств"
    }

    private func daysLabel(_ days: Int) -> String {
        let word = switch (days % 10, days % 100) {
        case (1, let h) where h != 11: "день"
        case (2 ... 4, let h) where !(12 ... 14).contains(h): "дня"
        default: "дней"
        }
        return "\(days) \(word)"
    }
}

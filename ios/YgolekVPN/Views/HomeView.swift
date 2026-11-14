import NetworkExtension
import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var model: AppModel
    @EnvironmentObject private var vpn: VPNController
    @Environment(\.openURL) private var openURL

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                HStack {
                    Header()
                    StatusPill(status: vpn.status)
                }
                PowerSection()
                    .padding(.vertical, 8)

                if let error = vpn.lastError ?? model.message {
                    Text(error)
                        .font(.footnote)
                        .foregroundStyle(Theme.danger)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(12)
                        .background(Theme.danger.opacity(0.1), in: RoundedRectangle(cornerRadius: 12, style: .continuous))
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
                .foregroundStyle(Theme.muted)
                .padding(.horizontal, 4)
            }
            .padding(20)
        }
        .refreshable { await model.loadAccount() }
    }
}

private struct StatusPill: View {
    let status: NEVPNStatus

    var body: some View {
        let (text, color): (String, Color) = switch status {
        case .connected: ("Защищено", Theme.success)
        case .connecting, .reasserting: ("Подключение", Theme.accent2)
        case .disconnecting: ("Отключение", Theme.muted)
        default: ("Отключено", Theme.muted)
        }
        HStack(spacing: 6) {
            Circle().fill(color).frame(width: 7, height: 7)
            Text(text).font(.caption).foregroundStyle(color)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 5)
        .background(Theme.panel2, in: Capsule())
        .overlay(Capsule().stroke(Theme.line))
    }
}

private struct PowerSection: View {
    @EnvironmentObject private var model: AppModel
    @EnvironmentObject private var vpn: VPNController
    @State private var pulse = false

    private var connected: Bool { vpn.status == .connected }
    private var busy: Bool { vpn.status == .connecting || vpn.status == .disconnecting || vpn.status == .reasserting }

    var body: some View {
        VStack(spacing: 10) {
            Button(action: toggle) {
                ZStack {
                    Circle()
                        .fill(connected ? Theme.success : Theme.panel2)
                        .overlay(Circle().stroke(connected ? Theme.success : Theme.accent, lineWidth: 3))
                        .overlay(Circle().inset(by: 12).stroke(Color.white.opacity(0.1)))
                        .shadow(color: (connected ? Theme.success : Theme.accent).opacity(busy && pulse ? 0.25 : 0.6),
                                radius: 34)
                    Image(systemName: "power")
                        .font(.system(size: 46, weight: .medium))
                        .foregroundStyle(.white)
                }
                .frame(width: 150, height: 150)
            }
            .buttonStyle(.plain)
            .disabled(busy || (!vpn.isActive && model.selectedServer == nil))
            .animation(.easeInOut(duration: 0.7).repeatForever(), value: pulse)
            .onAppear { pulse = true }

            Text(title)
                .font(.system(size: 24, weight: .semibold))
                .padding(.top, 6)
            TimelineView(.periodic(from: .now, by: 1)) { context in
                Text(subtitle(now: context.date))
                    .font(.subheadline)
                    .foregroundStyle(Theme.muted)
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
        return model.servers.isEmpty ? "Загружаем серверы…" : "Выбери сервер и нажми кнопку"
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
            Text("СЕРВЕРЫ")
                .font(.caption.weight(.semibold))
                .foregroundStyle(Theme.muted)
                .padding(.bottom, 10)
            if model.servers.isEmpty {
                Text(model.account?.subscription == nil ? "Серверы появятся после оформления подписки." : "Загрузка…")
                    .font(.subheadline)
                    .foregroundStyle(Theme.muted)
            }
            VStack(spacing: 8) {
                ForEach(model.servers) { server in
                    let selected = server == model.selectedServer
                    Button {
                        model.selectedServer = server
                    } label: {
                        HStack(spacing: 12) {
                            Image(systemName: "globe").foregroundStyle(Theme.muted)
                            Text(server.displayName).foregroundStyle(.white)
                            Spacer()
                            if selected {
                                Image(systemName: "checkmark").foregroundStyle(Theme.accent2)
                            }
                        }
                        .padding(.horizontal, 14)
                        .padding(.vertical, 13)
                        .background(selected ? Theme.accent.opacity(0.1) : Theme.panel2,
                                    in: RoundedRectangle(cornerRadius: 14, style: .continuous))
                        .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous)
                            .stroke(selected ? Theme.accent : Theme.line))
                    }
                    .buttonStyle(.plain)
                    .disabled(vpn.isActive)
                    .opacity(vpn.isActive && !selected ? 0.6 : 1)
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
                VStack(alignment: .leading, spacing: 4) {
                    Text("ПОДПИСКА")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(Theme.muted)
                    Text(title).font(.system(size: 18, weight: .semibold))
                    Text(details).font(.footnote).foregroundStyle(Theme.muted)
                }
                Spacer()
                Button(model.account?.subscription == nil ? "Оформить" : "Продлить") {
                    guard let account = model.account else { return }
                    let url = account.subscription == nil ? account.botUrl : account.renewUrl
                    if let url = URL(string: url) { openURL(url) }
                }
                .font(.subheadline)
                .padding(.horizontal, 14)
                .padding(.vertical, 9)
                .background(Theme.panel2, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
                .overlay(RoundedRectangle(cornerRadius: 12, style: .continuous).stroke(Theme.line))
                .foregroundStyle(.white)
            }
            if model.account?.subscription != nil {
                ProgressView(value: Double(min(daysLeft, 30)), total: 30)
                    .tint(daysLeft <= 3 ? Theme.danger : Theme.accent)
                    .padding(.top, 14)
            }
        }
    }

    private var daysLeft: Int {
        guard let expires = model.account?.subscription?.expiresAt else { return 0 }
        return max(0, Int((expires.timeIntervalSinceNow / 86400).rounded(.up)))
    }

    private var title: String {
        guard let expires = model.account?.subscription?.expiresAt else { return "Нет активной подписки" }
        return "Активна до \(expires.formatted(.dateTime.day(.twoDigits).month(.twoDigits).year()))"
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

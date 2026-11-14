import SwiftUI

@main
struct YgolekVPNApp: App {
    @StateObject private var model = AppModel()
    @StateObject private var vpn = VPNController()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(model)
                .environmentObject(vpn)
                .preferredColorScheme(.dark)
                .task { await model.start() }
        }
    }
}

/// Цвета как на сайте (site/tailwind.config.ts) и в Windows-клиенте
enum Theme {
    static let ink = Color(red: 8 / 255, green: 13 / 255, blue: 23 / 255)
    static let panel = Color(red: 14 / 255, green: 21 / 255, blue: 36 / 255)
    static let panel2 = Color(red: 19 / 255, green: 28 / 255, blue: 47 / 255)
    static let line = Color.white.opacity(0.14)
    static let muted = Color(red: 139 / 255, green: 151 / 255, blue: 173 / 255)
    static let accent = Color(red: 47 / 255, green: 123 / 255, blue: 255 / 255)
    static let accent2 = Color(red: 91 / 255, green: 155 / 255, blue: 255 / 255)
    static let success = Color(red: 34 / 255, green: 197 / 255, blue: 94 / 255)
    static let danger = Color(red: 248 / 255, green: 113 / 255, blue: 113 / 255)

    static let supportURL = URL(string: "https://t.me/ygolek_support")!
}

struct Card<Content: View>: View {
    @ViewBuilder var content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 0) { content }
            .padding(18)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Theme.panel, in: RoundedRectangle(cornerRadius: 20, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 20, style: .continuous).stroke(Theme.line))
    }
}

struct RootView: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        ZStack {
            Theme.ink.ignoresSafeArea()
            // мягкое синее свечение сверху, как на сайте
            RadialGradient(colors: [Theme.accent.opacity(0.22), .clear], center: .top, startRadius: 0, endRadius: 360)
                .ignoresSafeArea()

            switch model.screen {
            case .loading:
                ProgressView().tint(Theme.accent2)
            case .login:
                LoginView()
            case .home:
                HomeView()
            }
        }
    }
}

struct Header: View {
    var body: some View {
        HStack(spacing: 10) {
            Image("Logo")
                .resizable()
                .frame(width: 34, height: 34)
                .clipShape(RoundedRectangle(cornerRadius: 9, style: .continuous))
            Text("Ygolek VPN").font(.system(size: 19, weight: .semibold))
            Spacer()
        }
    }
}

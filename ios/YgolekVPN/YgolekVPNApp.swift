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
                .tint(.white)
                .task { await model.start() }
        }
    }
}

/// Чёрно-белая палитра: всё строится на белом с разной прозрачностью поверх чёрного
enum Theme {
    static let background = Color.black
    static let primary = Color.white
    static let secondary = Color.white.opacity(0.6)
    static let tertiary = Color.white.opacity(0.35)
    static let stroke = Color.white.opacity(0.16)
    static let fill = Color.white.opacity(0.06)
    // единственный цветной акцент — ошибки, чтобы их было видно
    static let danger = Color(red: 1, green: 0.42, blue: 0.42)

    static let supportURL = URL(string: "https://t.me/ygolek_support")!
}

// MARK: - Liquid Glass

extension View {
    /// Стекло Liquid Glass на iOS 26+, на старых iOS — матовое стекло с тонкой рамкой.
    @ViewBuilder
    func glass<S: Shape>(in shape: S, interactive: Bool = false) -> some View {
        #if compiler(>=6.2)
            if #available(iOS 26.0, *) {
                self.glassEffect(interactive ? .regular.interactive() : .regular, in: shape)
            } else {
                self.background(.ultraThinMaterial, in: shape)
                    .overlay(shape.stroke(Theme.stroke, lineWidth: 1))
            }
        #else
            self.background(.ultraThinMaterial, in: shape)
                .overlay(shape.stroke(Theme.stroke, lineWidth: 1))
        #endif
    }

    func glassCard(cornerRadius: CGFloat = 26) -> some View {
        glass(in: RoundedRectangle(cornerRadius: cornerRadius, style: .continuous))
    }
}

struct Card<Content: View>: View {
    @ViewBuilder var content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 0) { content }
            .padding(18)
            .frame(maxWidth: .infinity, alignment: .leading)
            .glassCard()
    }
}

struct SectionLabel: View {
    let text: String

    var body: some View {
        Text(text)
            .font(.caption2.weight(.semibold))
            .tracking(1.2)
            .foregroundStyle(Theme.tertiary)
    }
}

/// Белая кнопка с чёрным текстом — главное действие на экране
struct PrimaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.headline)
            .foregroundStyle(.black)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 16)
            .background(.white, in: Capsule())
            .scaleEffect(configuration.isPressed ? 0.97 : 1)
            .opacity(configuration.isPressed ? 0.85 : 1)
            .animation(.spring(response: 0.25, dampingFraction: 0.8), value: configuration.isPressed)
    }
}

/// Стеклянная кнопка-капсула — второстепенные действия
struct GlassButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.subheadline.weight(.medium))
            .foregroundStyle(Theme.primary)
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .glass(in: Capsule(), interactive: true)
            .scaleEffect(configuration.isPressed ? 0.96 : 1)
            .animation(.spring(response: 0.25, dampingFraction: 0.8), value: configuration.isPressed)
    }
}

// MARK: - Экраны

struct RootView: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        ZStack {
            Backdrop()
            switch model.screen {
            case .loading:
                ProgressView().tint(.white)
            case .login:
                LoginView()
            case .home:
                HomeView()
            }
        }
    }
}

/// Чёрный фон с мягкими светлыми пятнами — стеклу нужно, что «преломлять»
struct Backdrop: View {
    var body: some View {
        ZStack {
            Theme.background
            Circle()
                .fill(Color.white.opacity(0.13))
                .frame(width: 340, height: 340)
                .blur(radius: 90)
                .offset(x: -110, y: -300)
            Circle()
                .fill(Color.white.opacity(0.08))
                .frame(width: 300, height: 300)
                .blur(radius: 100)
                .offset(x: 140, y: 120)
            Circle()
                .fill(Color.white.opacity(0.06))
                .frame(width: 260, height: 260)
                .blur(radius: 90)
                .offset(x: -80, y: 420)
        }
        .ignoresSafeArea()
    }
}

struct Header: View {
    var body: some View {
        HStack(spacing: 10) {
            Image("Logo")
                .resizable()
                .frame(width: 34, height: 34)
                .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
            Text("Ygolek")
                .font(.system(size: 21, weight: .bold))
                .foregroundStyle(Theme.primary)
            Spacer()
        }
    }
}

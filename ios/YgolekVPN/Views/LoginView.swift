import SwiftUI

struct LoginView: View {
    @EnvironmentObject private var model: AppModel
    @Environment(\.openURL) private var openURL
    @State private var pulse = false

    var body: some View {
        VStack(spacing: 0) {
            Header()
            Spacer()

            VStack(spacing: 18) {
                Image(systemName: "paperplane.fill")
                    .font(.system(size: 34, weight: .medium))
                    .foregroundStyle(Theme.primary)
                    .frame(width: 84, height: 84)
                    .glass(in: Circle())

                VStack(spacing: 8) {
                    Text("Вход через Telegram")
                        .font(.system(size: 26, weight: .bold))
                    Text("Откроется бот и спросит, подтверждаешь ли ты вход на этом устройстве. Нажми «Войти» и возвращайся сюда.")
                        .font(.subheadline)
                        .foregroundStyle(Theme.secondary)
                        .multilineTextAlignment(.center)
                }

                Button("Открыть Telegram") {
                    if let url = model.loginBotURL { openURL(url) }
                }
                .buttonStyle(PrimaryButtonStyle())
                .disabled(model.loginBotURL == nil)
                .opacity(model.loginBotURL == nil ? 0.5 : 1)
                .padding(.top, 4)

                HStack(spacing: 8) {
                    Circle()
                        .fill(Theme.primary)
                        .frame(width: 6, height: 6)
                        .opacity(model.loginFailed ? 0.35 : (pulse ? 0.2 : 1))
                        .animation(.easeInOut(duration: 0.8).repeatForever(), value: pulse)
                    Text(model.loginStatus)
                        .font(.footnote)
                        .foregroundStyle(Theme.secondary)
                }

                if model.loginFailed {
                    Button("Попробовать снова") { model.startLogin() }
                        .buttonStyle(GlassButtonStyle())
                }
            }
            .padding(24)
            .glassCard(cornerRadius: 32)

            Spacer()
            Link("Поддержка · @ygolek_support", destination: Theme.supportURL)
                .font(.footnote)
                .foregroundStyle(Theme.tertiary)
        }
        .padding(20)
        .onAppear { pulse = true }
    }
}

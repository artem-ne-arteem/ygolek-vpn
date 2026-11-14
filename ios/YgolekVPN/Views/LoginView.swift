import SwiftUI

struct LoginView: View {
    @EnvironmentObject private var model: AppModel
    @Environment(\.openURL) private var openURL
    @State private var pulse = false

    var body: some View {
        VStack(spacing: 0) {
            Header().padding(.bottom, 24)
            Spacer()
            Card {
                VStack(spacing: 14) {
                    Image(systemName: "paperplane.circle.fill")
                        .font(.system(size: 64))
                        .foregroundStyle(Theme.accent)
                    Text("Вход через Telegram")
                        .font(.system(size: 24, weight: .semibold))
                    Text("Нажми кнопку — откроется бот и спросит, подтверждаешь ли ты вход на этом устройстве. Нажми там «Войти» и возвращайся сюда.")
                        .font(.subheadline)
                        .foregroundStyle(Theme.muted)
                        .multilineTextAlignment(.center)

                    Button {
                        if let url = model.loginBotURL { openURL(url) }
                    } label: {
                        Text("Открыть Telegram")
                            .font(.headline)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 15)
                            .background(Theme.accent, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
                            .foregroundStyle(.white)
                    }
                    .disabled(model.loginBotURL == nil)
                    .opacity(model.loginBotURL == nil ? 0.5 : 1)
                    .padding(.top, 6)

                    HStack(spacing: 8) {
                        Circle()
                            .fill(model.loginFailed ? Theme.muted : Theme.accent2)
                            .frame(width: 7, height: 7)
                            .opacity(model.loginFailed ? 1 : (pulse ? 0.25 : 1))
                            .animation(.easeInOut(duration: 0.8).repeatForever(), value: pulse)
                        Text(model.loginStatus)
                            .font(.footnote)
                            .foregroundStyle(Theme.muted)
                    }

                    if model.loginFailed {
                        Button("Попробовать снова") { model.startLogin() }
                            .font(.subheadline.weight(.medium))
                            .foregroundStyle(Theme.accent2)
                    }
                }
                .frame(maxWidth: .infinity)
            }
            Spacer()
            Link("Поддержка: @ygolek_support", destination: Theme.supportURL)
                .font(.footnote)
                .foregroundStyle(Theme.muted)
        }
        .padding(20)
        .onAppear { pulse = true }
    }
}

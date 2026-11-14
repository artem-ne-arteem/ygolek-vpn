import Foundation
import Security
import UIKit

/// Токен входа — в Keychain, прочие мелочи — в UserDefaults.
enum Storage {
    private static let tokenAccount = "app-token"

    static var token: String? {
        get {
            let query: [String: Any] = [
                kSecClass as String: kSecClassGenericPassword,
                kSecAttrAccount as String: tokenAccount,
                kSecReturnData as String: true,
                kSecMatchLimit as String: kSecMatchLimitOne,
            ]
            var item: CFTypeRef?
            guard SecItemCopyMatching(query as CFDictionary, &item) == errSecSuccess,
                  let data = item as? Data
            else { return nil }
            return String(data: data, encoding: .utf8)
        }
        set {
            let query: [String: Any] = [
                kSecClass as String: kSecClassGenericPassword,
                kSecAttrAccount as String: tokenAccount,
            ]
            SecItemDelete(query as CFDictionary)
            guard let newValue, let data = newValue.data(using: .utf8) else { return }
            var add = query
            add[kSecValueData as String] = data
            add[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlock
            SecItemAdd(add as CFDictionary, nil)
        }
    }

    static var lastServer: String? {
        get { UserDefaults.standard.string(forKey: "last-server") }
        set { UserDefaults.standard.set(newValue, forKey: "last-server") }
    }

    /// Постоянный id устройства — по нему панель считает устройства в подписке
    static var deviceId: String {
        if let saved = UserDefaults.standard.string(forKey: "device-id") { return saved }
        let id = UIDevice.current.identifierForVendor?.uuidString ?? UUID().uuidString
        UserDefaults.standard.set(id, forKey: "device-id")
        return id
    }
}

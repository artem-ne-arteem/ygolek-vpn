using System.IO;
using System.Security.Cryptography;
using System.Text;

namespace YgolekVpn.Services;

// Файлы приложения в %AppData%\YgolekVPN. Токен входа шифруется DPAPI —
// расшифровать его может только этот пользователь Windows.
public static class AppStorage
{
    public static readonly string Dir =
        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "YgolekVPN");

    private static string TokenPath => Path.Combine(Dir, "token.bin");
    private static string DeviceIdPath => Path.Combine(Dir, "device-id");
    private static string LastServerPath => Path.Combine(Dir, "last-server");

    /// <summary>Сервер, выбранный в прошлый раз (по названию из подписки).</summary>
    public static string? LastServer
    {
        get => File.Exists(LastServerPath) ? File.ReadAllText(LastServerPath).Trim() : null;
        set
        {
            Directory.CreateDirectory(Dir);
            File.WriteAllText(LastServerPath, value ?? "");
        }
    }

    public static string? LoadToken()
    {
        try
        {
            if (!File.Exists(TokenPath)) return null;
            var data = ProtectedData.Unprotect(File.ReadAllBytes(TokenPath), null, DataProtectionScope.CurrentUser);
            return Encoding.UTF8.GetString(data);
        }
        catch (Exception)
        {
            return null;
        }
    }

    public static void SaveToken(string token)
    {
        Directory.CreateDirectory(Dir);
        var data = ProtectedData.Protect(Encoding.UTF8.GetBytes(token), null, DataProtectionScope.CurrentUser);
        File.WriteAllBytes(TokenPath, data);
    }

    public static void DeleteToken()
    {
        if (File.Exists(TokenPath)) File.Delete(TokenPath);
    }

    /// <summary>Постоянный id этого компьютера — по нему панель считает устройства.</summary>
    public static string DeviceId()
    {
        Directory.CreateDirectory(Dir);
        if (File.Exists(DeviceIdPath))
        {
            var saved = File.ReadAllText(DeviceIdPath).Trim();
            if (saved.Length > 0) return saved;
        }
        var id = Guid.NewGuid().ToString("N");
        File.WriteAllText(DeviceIdPath, id);
        return id;
    }
}

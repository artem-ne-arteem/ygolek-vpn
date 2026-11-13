using System.Diagnostics;
using System.IO;

namespace YgolekVpn.Services;

/// <summary>Запускает и останавливает ядро sing-box (лежит рядом с приложением).</summary>
public sealed class SingBoxRunner
{
    private Process? _process;

    public static string CorePath => Path.Combine(AppContext.BaseDirectory, "sing-box.exe");
    public static string LogPath => Path.Combine(AppStorage.Dir, "sing-box.log");
    private static string ConfigPath => Path.Combine(AppStorage.Dir, "config.json");

    public bool IsRunning => _process is { HasExited: false };

    /// <summary>Ядро завершилось само (ошибка конфига, сервер недоступен и т.п.).</summary>
    public event Action<int>? Exited;

    public async Task StartAsync(VlessLink link)
    {
        if (!File.Exists(CorePath))
            throw new InvalidOperationException("Не найден sing-box.exe рядом с приложением — переустанови Ygolek VPN.");

        Stop();
        KillLeftovers();
        Directory.CreateDirectory(AppStorage.Dir);
        if (File.Exists(LogPath)) File.Delete(LogPath);
        await File.WriteAllTextAsync(ConfigPath, SingBoxConfig.Build(link, LogPath));

        var process = new Process
        {
            StartInfo = new ProcessStartInfo
            {
                FileName = CorePath,
                ArgumentList = { "run", "-c", ConfigPath, "-D", AppStorage.Dir },
                CreateNoWindow = true,
                UseShellExecute = false,
                WorkingDirectory = AppStorage.Dir,
            },
            EnableRaisingEvents = true,
        };
        process.Exited += (_, _) =>
        {
            if (ReferenceEquals(_process, process))
            {
                _process = null;
                Exited?.Invoke(process.ExitCode);
            }
        };
        process.Start();
        _process = process;

        // Если конфиг или адаптер не поднялись, ядро завершается почти сразу
        await Task.Delay(1500);
        if (process.HasExited)
        {
            _process = null;
            throw new InvalidOperationException($"Не удалось подключиться: {LastLogLine() ?? $"код {process.ExitCode}"}");
        }
    }

    public void Stop()
    {
        var process = _process;
        _process = null;
        if (process is { HasExited: false })
        {
            process.Kill(entireProcessTree: true);
            process.WaitForExit(3000);
        }
    }

    public static string? LastLogLine()
    {
        try
        {
            return File.Exists(LogPath) ? File.ReadLines(LogPath).LastOrDefault(l => l.Trim().Length > 0) : null;
        }
        catch (IOException)
        {
            return null;
        }
    }

    // ядро могло остаться после аварийного закрытия приложения — иначе адаптер будет занят
    private static void KillLeftovers()
    {
        foreach (var p in Process.GetProcessesByName("sing-box"))
        {
            try
            {
                if (string.Equals(p.MainModule?.FileName, CorePath, StringComparison.OrdinalIgnoreCase))
                    p.Kill(entireProcessTree: true);
            }
            catch (Exception)
            {
                // чужой или уже завершившийся процесс
            }
        }
    }
}

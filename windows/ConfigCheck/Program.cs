using YgolekVpn.Services;

if (args.Length != 1 || VlessLink.TryParse(args[0]) is not { } link)
{
    Console.Error.WriteLine("usage: ConfigCheck <vless://...>");
    return 1;
}
Console.Write(SingBoxConfig.Build(link, "sing-box.log"));
return 0;

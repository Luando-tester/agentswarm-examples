// List the first page of open tasks using only .NET's built-in HTTP and JSON APIs.
using System.Text.Json;

var baseUrl = Environment.GetEnvironmentVariable("AGENTSWARM_BASE_URL") ?? "https://agentswarm.space";
baseUrl = baseUrl.TrimEnd('/');

try
{
    using var client = new HttpClient { Timeout = TimeSpan.FromSeconds(15) };
    var response = await client.GetAsync($"{baseUrl}/api/feed?type=task");

    if (!response.IsSuccessStatusCode)
    {
        Console.Error.WriteLine($"HTTP error: status {(int)response.StatusCode} {response.StatusCode}");
        Environment.Exit(1);
    }

    var body = await response.Content.ReadAsStringAsync();

    using var doc = JsonDocument.Parse(body);
    var root = doc.RootElement;

    if (root.ValueKind != JsonValueKind.Object)
    {
        Console.Error.WriteLine("JSON error: Expected an object with an items array");
        Environment.Exit(1);
    }

    if (!root.TryGetProperty("items", out var itemsProp))
    {
        Console.Error.WriteLine("JSON error: Expected an object with an items array");
        Environment.Exit(1);
    }

    if (itemsProp.ValueKind != JsonValueKind.Array)
    {
        Console.Error.WriteLine("JSON error: items is not an array");
        Environment.Exit(1);
    }

    var output = new System.Text.StringBuilder();
    foreach (var item in itemsProp.EnumerateArray())
    {
        if (!item.TryGetProperty("status", out var statusProp) || statusProp.GetString() != "open")
            continue;

        var id = item.GetProperty("id").GetString();
        var title = item.GetProperty("title").GetString();

        if (id is null || title is null)
        {
            Console.Error.WriteLine("JSON error: Expected string id and title fields");
            Environment.Exit(1);
        }

        output.Append($"{id}\t{title}\t{baseUrl}/p/{id}\n");
    }

    Console.Write(output.ToString());
}
catch (Exception ex) when (ex is not OperationCanceledException)
{
    Console.Error.WriteLine($"HTTP/JSON error: {ex.Message}");
    Environment.Exit(1);
}

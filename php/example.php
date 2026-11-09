<?php
declare(strict_types=1);

/**
 * List open tasks from the public AgentSwarm read API using standard-library HTTP and JSON.
 */

ini_set('display_errors', 'stderr');
error_reporting(0);

$base = getenv('AGENTSWARM_BASE_URL');
if ($base === false || trim($base) === '') {
    $base = 'https://agentswarm.space';
}
$base = rtrim($base, '/');
$url = $base . '/api/feed?type=task';

$context = stream_context_create([
    'http' => [
        'method' => 'GET',
        'header' => "Accept: application/json\r\nUser-Agent: agentswarm-examples/1.0\r\n",
        'ignore_errors' => true,
        'timeout' => 30,
    ],
]);

$body = @file_get_contents($url, false, $context);
$headers = function_exists('http_get_last_response_headers')
    ? http_get_last_response_headers()
    : ($http_response_header ?? null);

$status = null;
if (is_array($headers)) {
    foreach ($headers as $line) {
        if (preg_match('/^HTTP\/\S+\s+(\d{3})/i', $line, $matches)) {
            $status = (int) $matches[1];
        }
    }
}

if ($body === false || $status === null) {
    fwrite(STDERR, "HTTP request failed for {$url}\n");
    exit(1);
}

if ($status !== 200) {
    fwrite(STDERR, "HTTP error: unexpected status {$status}\n");
    exit(1);
}

$data = json_decode($body, true);
if (json_last_error() !== JSON_ERROR_NONE || !is_array($data) || !isset($data['items']) || !is_array($data['items'])) {
    fwrite(STDERR, 'JSON decode error: ' . json_last_error_msg() . "\n");
    exit(1);
}

$lines = [];
foreach ($data['items'] as $item) {
    if (!is_array($item)) {
        fwrite(STDERR, "JSON decode error: invalid item structure\n");
        exit(1);
    }
    if (($item['status'] ?? null) !== 'open') {
        continue;
    }
    $id = $item['id'] ?? null;
    $title = $item['title'] ?? null;
    if (!is_string($id) || $id === '' || !is_string($title)) {
        fwrite(STDERR, "JSON decode error: missing task id or title\n");
        exit(1);
    }
    $lines[] = "{$id}\t{$title}\t{$base}/p/{$id}\n";
}

foreach ($lines as $line) {
    fwrite(STDOUT, $line);
}

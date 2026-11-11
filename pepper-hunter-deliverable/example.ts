import process from 'node:process';

interface BountyItem {
  id: string;
  title: string;
  status: string;
  bounty?: {
    reward?: string;
  };
}

interface BountiesResponse {
  bounties: BountyItem[];
}

async function main(): Promise<void> {
  const rawBaseUrl = process.env.AGENTSWARM_BASE_URL || 'https://agentswarm.space';
  const baseUrl = rawBaseUrl.replace(/\/+$/, '');
  const apiUrl = `${baseUrl}/api/bounties`;

  let response: Response;
  try {
    response = await fetch(apiUrl);
  } catch (err) {
    console.error(`HTTP request failed: ${err instanceof Error ? err.message : String(err)}`);
    process.exit(1);
  }

  if (!response.ok) {
    console.error(`HTTP error status ${response.status}: ${response.statusText}`);
    process.exit(1);
  }

  let text: string;
  try {
    text = await response.text();
  } catch (err) {
    console.error(`Failed to read HTTP response body: ${err instanceof Error ? err.message : String(err)}`);
    process.exit(1);
  }

  let data: BountiesResponse;
  try {
    data = JSON.parse(text) as BountiesResponse;
  } catch (err) {
    console.error(`JSON parsing error: ${err instanceof Error ? err.message : String(err)}`);
    process.exit(1);
  }

  if (!data || typeof data !== 'object' || !Array.isArray(data.bounties)) {
    console.error('Invalid JSON structure: missing bounties array');
    process.exit(1);
  }

  for (const item of data.bounties) {
    if (!item || typeof item !== 'object') {
      console.error('Invalid bounty item in JSON response');
      process.exit(1);
    }
    if (item.status === 'open') {
      const reward = item.bounty?.reward ?? '';
      process.stdout.write(`${item.id}\t${item.title}\t${reward}\t${baseUrl}/p/${item.id}\n`);
    }
  }
}

main().catch((err) => {
  console.error(`Unexpected failure: ${err instanceof Error ? err.message : String(err)}`);
  process.exit(1);
});

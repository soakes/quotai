import './style.css';

const fallbackHighlights = [
  'Show exact rolling quota reset times',
  'Render readable terminal and JSON output',
  'Ship a signed Debian and APT install path',
];

function normalizeHighlights(value) {
  if (!Array.isArray(value)) {
    return fallbackHighlights;
  }

  const highlights = value
    .map((item) => `${item ?? ''}`.trim())
    .filter(Boolean)
    .slice(0, 3);

  return highlights.length > 0 ? highlights : fallbackHighlights;
}

function parseBuildHighlights(value) {
  try {
    return normalizeHighlights(JSON.parse(value || '[]'));
  } catch {
    return fallbackHighlights;
  }
}

function hasBuildHighlights(value) {
  try {
    const parsed = JSON.parse(value || '[]');
    return Array.isArray(parsed) && parsed.some((item) => `${item ?? ''}`.trim() !== '');
  } catch {
    return false;
  }
}

const buildHighlightsValue = process.env.PUBLIC_RELEASE_HIGHLIGHTS_JSON;
const hasExplicitBuildHighlights = hasBuildHighlights(buildHighlightsValue);

const defaultMetadata = {
  siteUrl: process.env.PUBLIC_SITE_URL.replace(/\/?$/, '/'),
  releaseVersion: process.env.PUBLIC_RELEASE_VERSION,
  commit: process.env.PUBLIC_COMMIT,
  buildDate: process.env.PUBLIC_BUILD_DATE,
  aptFingerprint: process.env.PUBLIC_APT_FINGERPRINT,
  releaseHighlights: parseBuildHighlights(buildHighlightsValue),
};

function formatBuildDate(value) {
  const parsedBuildDate = new Date(value);
  return Number.isNaN(parsedBuildDate.valueOf())
    ? value
    : `${new Intl.DateTimeFormat('en-GB', {
        dateStyle: 'long',
        timeStyle: 'short',
        timeZone: 'UTC',
      }).format(parsedBuildDate)} UTC`;
}

function parseStableTag(value) {
  const match = `${value}`.match(/^v(\d+)\.(\d+)\.(\d+)$/);
  return match ? match.slice(1).map((part) => Number.parseInt(part, 10)) : null;
}

function compareStableTags(left, right) {
  const leftParts = parseStableTag(left);
  const rightParts = parseStableTag(right);

  if (!leftParts || !rightParts) {
    return 0;
  }

  for (let index = 0; index < leftParts.length; index += 1) {
    if (leftParts[index] !== rightParts[index]) {
      return leftParts[index] - rightParts[index];
    }
  }

  return 0;
}

function normalizeMetadata(value = {}) {
  const siteUrl = `${value.site_url || value.siteUrl || defaultMetadata.siteUrl}`.replace(/\/?$/, '/');
  const releaseVersion = `${value.release_version || value.releaseVersion || defaultMetadata.releaseVersion}`;
  const commit = `${value.commit || defaultMetadata.commit}`;
  const buildDate = `${value.build_date || value.buildDate || defaultMetadata.buildDate}`;
  const aptFingerprint = `${value.apt_fingerprint || value.aptFingerprint || defaultMetadata.aptFingerprint}`;

  return {
    siteUrl,
    releaseVersion,
    releaseNumber: releaseVersion.replace(/^v/, ''),
    commit,
    shortCommit: commit.length > 10 ? commit.slice(0, 7) : commit,
    formattedBuildDate: formatBuildDate(buildDate),
    aptFingerprint,
    releaseHighlights: normalizeHighlights(value.release_highlights || value.releaseHighlights),
  };
}

function shouldRenderFetchedMetadata(metadata) {
  if (parseStableTag(defaultMetadata.releaseVersion) && !parseStableTag(metadata.releaseVersion)) {
    return false;
  }

  return compareStableTags(metadata.releaseVersion, defaultMetadata.releaseVersion) >= 0;
}

function mergeFetchedMetadata(metadata) {
  if (hasExplicitBuildHighlights && metadata.releaseVersion === defaultMetadata.releaseVersion) {
    return {
      ...metadata,
      releaseHighlights: defaultMetadata.releaseHighlights,
    };
  }

  return metadata;
}

function renderMetadata(metadata) {
  const mappings = {
    'ui-version': metadata.releaseVersion,
    'ui-commit': metadata.shortCommit,
    'ui-date': metadata.formattedBuildDate,
    'ui-fingerprint': metadata.aptFingerprint,
    'footer-version': metadata.releaseVersion,
    'footer-commit': metadata.shortCommit,
  };

  for (const [id, value] of Object.entries(mappings)) {
    const element = document.getElementById(id);
    if (element) {
      element.textContent = value;
    }
  }

  const siteUrlLink = document.getElementById('site-url-link');
  if (siteUrlLink) {
    siteUrlLink.href = metadata.siteUrl;
  }

  const aptLink = document.getElementById('nav-apt-link');
  if (aptLink) {
    aptLink.href = metadata.siteUrl;
  }

  const aptCodeContainer = document.getElementById('apt-code-container');
  if (aptCodeContainer) {
    aptCodeContainer.innerHTML = `
<pre><code>sudo install -d -m 0755 /etc/apt/keyrings
curl -fsSL ${metadata.siteUrl}quotai-archive-keyring.gpg \\
  | sudo tee /etc/apt/keyrings/quotai-archive-keyring.gpg >/dev/null

sudo tee /etc/apt/sources.list.d/quotai.sources >/dev/null &lt;&lt;'EOF'
Types: deb deb-src
URIs: ${metadata.siteUrl}
Suites: stable
Components: main
Signed-By: /etc/apt/keyrings/quotai-archive-keyring.gpg
EOF

sudo apt update && sudo apt install quotai</code></pre>`;
  }

  const archiveCodeContainer = document.getElementById('archive-code-container');
  if (archiveCodeContainer) {
    archiveCodeContainer.innerHTML = `
<pre><code>curl -fsSL https://github.com/soakes/quotai/releases/latest/download/quotai-${metadata.releaseNumber}.tar.gz -o quotai.tar.gz
tar -xzf quotai.tar.gz
sudo install -m 0755 quotai-${metadata.releaseNumber}/quotai.py /usr/local/bin/quotai</code></pre>`;
  }

  const highlightsList = document.getElementById('ui-highlights');
  if (highlightsList) {
    highlightsList.replaceChildren(
      ...metadata.releaseHighlights.map((highlight) => {
        const item = document.createElement('li');
        const match = highlight.match(/^(.*\()([0-9a-f]{7,40})\)$/);
        if (match) {
          item.appendChild(document.createTextNode(match[1]));
          const link = document.createElement('a');
          link.href = `https://github.com/soakes/quotai/commit/${match[2]}`;
          link.textContent = `${match[2]})`;
          link.target = '_blank';
          link.rel = 'noopener';
          item.appendChild(link);
        } else {
          item.textContent = highlight;
        }
        return item;
      }),
    );
  }
}

document.addEventListener('DOMContentLoaded', () => {
  renderMetadata(normalizeMetadata(defaultMetadata));

  fetch('./website-metadata.json', { cache: 'no-store' })
    .then((response) => {
      if (!response.ok) {
        return null;
      }
      return response.json();
    })
    .then((metadata) => {
      if (!metadata) {
        return;
      }
      const normalizedMetadata = normalizeMetadata(metadata);
      if (shouldRenderFetchedMetadata(normalizedMetadata)) {
        renderMetadata(mergeFetchedMetadata(normalizedMetadata));
      }
    })
    .catch(() => {
      // Keep build-time defaults when metadata is unavailable in local previews.
    });
});

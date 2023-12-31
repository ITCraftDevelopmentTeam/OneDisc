---
sidebar: auto
---

# 下载

| 最新测试版 | 最新稳定版 |
|------------|------------|
| {{ betaVersion }} | {{ stableVersion }} |

## 稳定版

<div v-html="stableArtifacts"></div>

## 测试版

> 下载这些内容可能需要先在 [GitHub](https://github.com) 上登陆

<div v-html="betaArtifacts"></div>

<script setup>
import { ref, onMounted } from 'vue';

const betaVersion = ref('');
const stableVersion = ref('');
const betaArtifacts = ref('');
const stableArtifacts = ref('');

onMounted(async () => {
  betaVersion.value = await fetchBetaVersion();
  stableVersion.value = await fetchStableVersion();
  betaArtifacts.value = await fetchBetaArtifacts();
  stableArtifacts.value = await fetchStableArtifacts();
});


async function fetchBetaVersion() {
  const beta = await (await fetch("https://onedisc.itcdt.top/version.json")).json();
  return beta.beta;
}

async function fetchBetaArtifacts() {
  
  const response = await fetch("https://onedisc.itcdt.top/artifacts.json");
  const data = await response.json();
  let html = "<ul>";
  data.artifacts.forEach(function(item, index, array) {
    html += `<li><a href="https://github.com/ITCraftDevelopmentTeam/OneDisc/actions/runs/${item.workflow_run.id}/artifacts/${item.id}">${item.name}</a></li>`;
  })
  html += "</ul>";
  return html;
}

async function fetchStableArtifacts() {
  const response = await fetch("https://onedisc.itcdt.top/release.json");
  const data = await response.json();
  let html = "<ul>";
  data.assets.forEach(function(item, index, array) {
    html += `<li><a href="${item.browser_download_url}">${item.name}</a></li>`;
  })
  html += "</ul>";
  return html;
}

async function fetchStableVersion() {
  const beta = await (await fetch("https://onedisc.itcdt.top/version.json")).json();
  return beta.stable;
}

</script>


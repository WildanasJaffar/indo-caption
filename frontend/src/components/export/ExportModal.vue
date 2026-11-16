<template>
  <div v-if="isOpen" class="modal modal-open">
    <div class="modal-box bg-[#11131a] border border-[#212534] text-slate-200 max-w-xl shadow-2xl rounded-2xl p-5">
      <!-- Header -->
      <div class="flex items-center justify-between pb-3 border-b border-[#1d212c]">
        <div class="flex items-center gap-2">
          <div class="w-2 h-2 rounded-full bg-emerald-400"></div>
          <h3 class="font-bold text-sm tracking-wide text-white uppercase">
            Export Subtitle
          </h3>
        </div>
        <button
          class="w-6 h-6 rounded-md bg-[#161822] hover:bg-[#202534] text-slate-400 hover:text-white flex items-center justify-center transition-colors cursor-pointer"
          @click="$emit('close')"
        >
          ✕
        </button>
      </div>

      <!-- Feedback Toast Banner -->
      <div v-if="feedbackMsg" class="mt-3 p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center justify-between font-mono">
        <span class="truncate">{{ feedbackMsg }}</span>
        <button class="text-emerald-400 hover:text-white cursor-pointer ml-2" @click="feedbackMsg = ''">✕</button>
      </div>

      <!-- Export Options List -->
      <div class="flex flex-col gap-3 my-4 text-xs">
        <!-- 1. CapCut Word-Level Special Card -->
        <div class="p-3.5 rounded-xl bg-gradient-to-r from-[#171610] to-[#13151c] border border-[#ffb800]/60 flex items-center justify-between gap-3 shadow-md shadow-[#ffb800]/5">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-lg bg-[#ffb800] text-black flex items-center justify-center font-black text-xs shadow-inner">
              CC
            </div>
            <div>
              <div class="flex items-center gap-2">
                <span class="font-bold text-xs text-white">Word-Level SRT (Khusus CapCut)</span>
                <span class="text-[9px] font-mono font-bold text-black bg-[#ffb800] px-1.5 py-0.2 rounded uppercase">
                  DIREKOMENDASIKAN
                </span>
              </div>
              <p class="text-[11px] text-slate-400 mt-0.5 font-normal">
                Timestamp presisi per kata. Impor ke CapCut untuk animasi pop-up kata per kata.
              </p>
            </div>
          </div>
          <button
            @click="downloadFile(getSrtWordsUrl, `${cleanName}_word_level.srt`)"
            :disabled="downloadingName !== null"
            class="studio-btn-primary px-3.5 py-1.5 rounded-md text-xs font-black uppercase tracking-wider flex items-center gap-1.5 shrink-0 cursor-pointer"
          >
            <Download class="w-3.5 h-3.5 text-black" />
            <span>{{ downloadingName === `${cleanName}_word_level.srt` ? 'Menyimpan...' : 'Download' }}</span>
          </button>
        </div>

        <!-- 2. Standard Subtitle Formats Grid -->
        <div class="grid grid-cols-2 gap-2">
          <!-- Standard SRT -->
          <div class="p-2.5 rounded-lg bg-[#0c0e14] border border-[#1e222f] flex items-center justify-between">
            <div>
              <span class="font-bold text-slate-200 block text-xs">Standard SRT (.srt)</span>
              <span class="text-[10px] text-slate-500">Format standar per baris</span>
            </div>
            <button
              @click="downloadFile(getSrtUrl, `${cleanName}_captions.srt`)"
              :disabled="downloadingName !== null"
              class="px-2.5 py-1 rounded bg-[#161822] hover:bg-[#222736] border border-[#262c3e] text-slate-300 hover:text-white text-[11px] font-bold cursor-pointer transition-all"
            >
              {{ downloadingName === `${cleanName}_captions.srt` ? '...' : 'Unduh' }}
            </button>
          </div>

          <!-- WebVTT -->
          <div class="p-2.5 rounded-lg bg-[#0c0e14] border border-[#1e222f] flex items-center justify-between">
            <div>
              <span class="font-bold text-slate-200 block text-xs">WebVTT (.vtt)</span>
              <span class="text-[10px] text-slate-500">Web player & YouTube</span>
            </div>
            <button
              @click="downloadFile(getVttUrl, `${cleanName}_captions.vtt`)"
              :disabled="downloadingName !== null"
              class="px-2.5 py-1 rounded bg-[#161822] hover:bg-[#222736] border border-[#262c3e] text-slate-300 hover:text-white text-[11px] font-bold cursor-pointer transition-all"
            >
              {{ downloadingName === `${cleanName}_captions.vtt` ? '...' : 'Unduh' }}
            </button>
          </div>

          <!-- ASS Styled -->
          <div class="p-2.5 rounded-lg bg-[#0c0e14] border border-[#1e222f] flex items-center justify-between">
            <div>
              <span class="font-bold text-slate-200 block text-xs">Styled ASS (.ass)</span>
              <span class="text-[10px] text-slate-500">Warna, font & stroke tersimpan</span>
            </div>
            <button
              @click="downloadFile(getAssUrl, `${cleanName}_styled.ass`)"
              :disabled="downloadingName !== null"
              class="px-2.5 py-1 rounded bg-[#161822] hover:bg-[#222736] border border-[#262c3e] text-slate-300 hover:text-white text-[11px] font-bold cursor-pointer transition-all"
            >
              {{ downloadingName === `${cleanName}_styled.ass` ? '...' : 'Unduh' }}
            </button>
          </div>

          <!-- Plain TXT -->
          <div class="p-2.5 rounded-lg bg-[#0c0e14] border border-[#1e222f] flex items-center justify-between">
            <div>
              <span class="font-bold text-slate-200 block text-xs">Transkrip TXT (.txt)</span>
              <span class="text-[10px] text-slate-500">Naskah teks tanpa timing</span>
            </div>
            <button
              @click="downloadFile(getTxtUrl, `${cleanName}_transcript.txt`)"
              :disabled="downloadingName !== null"
              class="px-2.5 py-1 rounded bg-[#161822] hover:bg-[#222736] border border-[#262c3e] text-slate-300 hover:text-white text-[11px] font-bold cursor-pointer transition-all"
            >
              {{ downloadingName === `${cleanName}_transcript.txt` ? '...' : 'Unduh' }}
            </button>
          </div>
        </div>
      </div>

      <div class="modal-action border-t border-[#1d212c] pt-3">
        <button
          class="px-3 py-1.5 rounded-md bg-[#161822] hover:bg-[#202534] text-slate-400 hover:text-white text-xs font-semibold cursor-pointer transition-colors"
          @click="$emit('close')"
        >
          Tutup
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { Download } from '@lucide/vue';

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  projectName: {
    type: String,
    default: 'video',
  },
  getSrtUrl: {
    type: String,
    default: '#',
  },
  getSrtWordsUrl: {
    type: String,
    default: '#',
  },
  getVttUrl: {
    type: String,
    default: '#',
  },
  getTxtUrl: {
    type: String,
    default: '#',
  },
  getAssUrl: {
    type: String,
    default: '#',
  },
});

defineEmits(['close']);

const cleanName = computed(() => {
  return (props.projectName || 'video').replace(/\.[^/.]+$/, '').replace(/[^a-zA-Z0-9_-]/g, '_');
});

const downloadingName = ref(null);
const feedbackMsg = ref('');

async function downloadFile(url, defaultFilename) {
  if (!url || url === '#') return;
  downloadingName.value = defaultFilename;

  try {
    // 1. PyWebView Desktop Native Save File Dialog
    if (typeof window !== 'undefined' && window.pywebview?.api?.download_url_to_file) {
      const savedPath = await window.pywebview.api.download_url_to_file(url, defaultFilename);
      if (savedPath) {
        feedbackMsg.value = `File tersimpan di: ${savedPath}`;
        setTimeout(() => { feedbackMsg.value = ''; }, 5000);
      }
      return;
    }

    // 2. Standard Browser Fallback (Blob fetch & trigger programmatic download)
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const blob = await response.blob();
    const objectUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = defaultFilename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(objectUrl);

    feedbackMsg.value = `Berhasil mengunduh ${defaultFilename}!`;
    setTimeout(() => { feedbackMsg.value = ''; }, 4000);
  } catch (err) {
    console.warn('Fallback direct download link:', err);
    window.location.href = url;
  } finally {
    downloadingName.value = null;
  }
}
</script>

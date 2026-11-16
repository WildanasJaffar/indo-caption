<template>
  <div class="h-screen w-screen flex flex-col bg-[#0b0c10] text-slate-100 overflow-hidden font-sans">
    <!-- Navbar -->
    <Navbar
      :project="currentProject"
      :hardware-info="hardwareInfo"
      :is-transcribing="isTranscribing"
      @open-import="isUploadModalOpen = true"
      @open-transcribe="isTranscribeModalOpen = true"
      @open-export="isExportModalOpen = true"
      @go-home="isUploadModalOpen = true"
      @delete-current="handleDeleteProject"
    />

    <!-- Main Workspace Studio (3 Panel Layout) -->
    <main v-if="currentProject" class="flex-1 min-h-0 p-2.5 grid grid-cols-12 gap-2.5 overflow-hidden">
      <!-- Panel 1: Video Player & Subtitle Overlay (Cols 4) -->
      <section class="col-span-12 lg:col-span-5 xl:col-span-4 h-full flex flex-col min-h-0">
        <VideoPlayer
          ref="videoPlayerRef"
          :video-src="videoStreamUrl"
          :subtitles="subtitles"
          :style-config="styleConfig"
          :seek-target="seekTarget"
          @time-update="onVideoTimeUpdate"
        />
      </section>

      <!-- Panel 2: Subtitle List & Editor (Cols 5) -->
      <section class="col-span-12 lg:col-span-4 xl:col-span-5 h-full flex flex-col min-h-0">
        <SubtitleList
          :subtitles="subtitles"
          :current-time="currentTime"
          @jump="jumpToTime"
          @update-subtitle="updateSubtitle"
          @delete-subtitle="deleteSubtitle"
          @add-subtitle="addSubtitle"
          @open-split="openSplitModal"
          @merge-down="mergeSubtitleDown"
          @resegment="resegmentSubtitles"
          @move-subtitle="handleMoveSubtitle"
          @reorder-indices="handleReorderSubtitles"
          @sort-by-time="handleSortByTime"
          @insert-after="handleInsertAfter"
        />
      </section>

      <!-- Panel 3: Caption Styling Controls & Presets (Cols 3) -->
      <section class="col-span-12 lg:col-span-3 xl:col-span-3 h-full flex flex-col min-h-0">
        <StylePanel
          v-model="styleConfig"
        />
      </section>
    </main>

    <!-- Welcome / Studio Landing Deck when no project is loaded -->
    <div v-else class="flex-1 flex flex-col items-center justify-center p-6 text-center select-none relative overflow-y-auto">
      <!-- Background Ambient Grid -->
      <div class="absolute inset-0 bg-[radial-gradient(#1c202d_1px,transparent_1px)] [background-size:24px_24px] opacity-40 pointer-events-none"></div>

      <div class="relative z-10 max-w-xl flex flex-col items-center">
        <!-- Live Caption Mockup Strip (Demonstrates the viral caption look) -->
        <div class="mb-6 p-4 rounded-2xl bg-[#12141c] border border-[#222736] shadow-2xl flex flex-col items-center gap-2">
          <div class="flex items-center gap-1.5 text-[10px] font-mono tracking-widest text-[#ffb800] uppercase font-bold">
            <span class="w-1.5 h-1.5 rounded-full bg-[#ffb800] animate-ping"></span>
            PREVIEW HASIL VIRAL CAPTION
          </div>
          <!-- Sample Viral Caption Preview -->
          <div class="bg-black/80 px-4 py-2 rounded-lg border border-[#242939] shadow-inner text-center">
            <span class="text-xl font-black text-[#FFE600] tracking-wide uppercase drop-shadow-[0_2px_4px_rgba(0,0,0,0.9)]" style="font-family: 'Poppins', sans-serif; -webkit-text-stroke: 1.5px black;">
              CEPAT PAHAM BERHITUNG
            </span>
          </div>
        </div>

        <!-- Headline & Value Proposition -->
        <h1 class="text-3xl sm:text-4xl font-black tracking-tight text-white uppercase">
          Indo<span class="text-[#ffb800]">Caption</span> Studio
        </h1>
        <p class="text-slate-400 mt-2 text-xs sm:text-sm leading-relaxed max-w-md font-medium">
          Editor caption otomatis lokal untuk kreator video Indonesia. 100% offline, tanpa kuota API, dan siap ekspor ke CapCut.
        </p>

        <!-- 3 Pillars Chips -->
        <div class="grid grid-cols-3 gap-2 mt-6 w-full max-w-md text-[11px] font-semibold text-slate-300">
          <div class="p-2.5 rounded-lg bg-[#14161f] border border-[#212634] flex flex-col items-center gap-1">
            <span class="text-[#ffb800] font-bold text-xs">⚡ 100% Offline</span>
            <span class="text-[10px] text-slate-500 text-center font-normal">Faster-Whisper lokal</span>
          </div>
          <div class="p-2.5 rounded-lg bg-[#14161f] border border-[#212634] flex flex-col items-center gap-1">
            <span class="text-emerald-400 font-bold text-xs">🎯 Presisi Kata</span>
            <span class="text-[10px] text-slate-500 text-center font-normal">Word-Level CapCut</span>
          </div>
          <div class="p-2.5 rounded-lg bg-[#14161f] border border-[#212634] flex flex-col items-center gap-1">
            <span class="text-sky-400 font-bold text-xs">🔒 Zero-Copy</span>
            <span class="text-[10px] text-slate-500 text-center font-normal">Buka instan file lokal</span>
          </div>
        </div>

        <!-- Big Trigger Button -->
        <button
          class="studio-btn-primary mt-8 px-8 py-3 rounded-xl text-sm font-black tracking-wider uppercase flex items-center gap-2 cursor-pointer"
          @click="isUploadModalOpen = true"
        >
          <FolderOpen class="w-4 h-4 text-black" />
          <span>Buka Video untuk Mulai</span>
        </button>

        <!-- Recent Projects Mini Deck -->
        <div v-if="projectList.length > 0" class="mt-8 w-full max-w-md flex flex-col gap-2 text-left">
          <span class="text-[10px] font-mono uppercase text-slate-500 font-bold tracking-wider">
            Project Terakhir:
          </span>
          <div class="flex flex-col gap-1.5 max-h-36 overflow-y-auto pr-1">
            <div
              v-for="p in projectList.slice(0, 3)"
              :key="p.id"
              class="p-2 rounded-lg bg-[#14161f] hover:bg-[#1c202c] border border-[#202534] hover:border-[#ffb800]/50 flex items-center justify-between cursor-pointer transition-all"
              @click="selectExistingProject(p)"
            >
              <div class="flex items-center gap-2 min-w-0">
                <Film class="w-3.5 h-3.5 text-[#ffb800] shrink-0" />
                <span class="text-xs font-semibold text-slate-200 truncate">{{ p.name }}</span>
              </div>
              <span class="text-[10px] font-mono text-slate-500 shrink-0">{{ formatDuration(p.duration) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <UploadModal
      :is-open="isUploadModalOpen"
      :existing-projects="projectList"
      :is-uploading="isUploading"
      :upload-pct="uploadProgress"
      @close="isUploadModalOpen = false"
      @upload="handleVideoUpload"
      @select-project="selectExistingProject"
      @delete-project="handleDeleteProject"
      @select-native-path="handleNativeFileSelect"
    />

    <TranscribeModal
      :is-open="isTranscribeModalOpen"
      :is-transcribing="isTranscribing"
      :progress-pct="transcribeProgress"
      :progress-status="transcribeStatus"
      :latest-segment-text="latestSegmentText"
      @close="isTranscribeModalOpen = false"
      @start="handleStartTranscribe"
    />

    <ExportModal
      :is-open="isExportModalOpen"
      :project-name="currentProject?.name || 'video'"
      :get-srt-url="currentProject ? exportApi.getSrtUrl(currentProject.id) : '#'"
      :get-srt-words-url="currentProject ? exportApi.getSrtWordsUrl(currentProject.id) : '#'"
      :get-vtt-url="currentProject ? exportApi.getVttUrl(currentProject.id) : '#'"
      :get-txt-url="currentProject ? exportApi.getTxtUrl(currentProject.id) : '#'"
      :get-ass-url="currentProject ? exportApi.getAssUrl(currentProject.id) : '#'"
      @close="isExportModalOpen = false"
    />

    <SplitModal
      :is-open="isSplitModalOpen"
      :item="splitTargetItem"
      @close="isSplitModalOpen = false"
      @confirm="handleConfirmSplit"
    />

    <!-- Toast Notification -->
    <transition enter-active-class="transition duration-200 ease-out" enter-from-class="opacity-0 translate-y-2" enter-to-class="opacity-100 translate-y-0" leave-active-class="transition duration-150 ease-in" leave-from-class="opacity-100 translate-y-0" leave-to-class="opacity-0 translate-y-2">
      <div v-if="toastMessage" class="toast toast-bottom toast-center z-50">
        <div class="alert alert-info bg-slate-900 border border-cyan-500/50 text-cyan-200 shadow-xl text-xs py-2 px-4">
          <span>{{ toastMessage }}</span>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { Subtitles, UploadCloud, FolderOpen, Film } from '@lucide/vue';
import { formatTimeHHMMSS } from './utils/timeFormatter.js';
import Navbar from './components/common/Navbar.vue';
import VideoPlayer from './components/preview/VideoPlayer.vue';
import SubtitleList from './components/editor/SubtitleList.vue';
import StylePanel from './components/styling/StylePanel.vue';
import UploadModal from './components/common/UploadModal.vue';
import TranscribeModal from './components/common/TranscribeModal.vue';
import ExportModal from './components/export/ExportModal.vue';
import SplitModal from './components/editor/SplitModal.vue';
import { projectApi, transcribeApi, subtitleApi, exportApi } from './api/client.js';

// Project & Video State
const currentProject = ref(null);
const projectList = ref([]);
const subtitles = ref([]);
const currentTime = ref(0);
const seekTarget = ref(null);
const hardwareInfo = ref(null);

// Modal States
const isUploadModalOpen = ref(false);
const isTranscribeModalOpen = ref(false);
const isExportModalOpen = ref(false);
const isSplitModalOpen = ref(false);
const splitTargetItem = ref(null);

// Process States
const isUploading = ref(false);
const uploadProgress = ref(0);
const isTranscribing = ref(false);
const transcribeProgress = ref(0);
const transcribeStatus = ref('Menyiapkan transkripsi...');
const latestSegmentText = ref('');
const toastMessage = ref('');

// Caption Styling State (Default requested by user)
const styleConfig = reactive({
  fontFamily: 'Poppins, sans-serif',
  fontSize: 22,
  textColor: '#FFE600',
  outlineColor: '#000000',
  outlineWidth: 2,
  shadowColor: '#000000',
  shadowDepth: 0,
  bgColor: '#000000',
  bgOpacity: 0.0,
  positionY: 78,
  isBold: true,
  textTransform: 'uppercase',
  highlightActiveWord: false,
  highlightColor: '#00F2FE',
});

const videoStreamUrl = computed(() => {
  if (!currentProject.value) return '';
  return `/api/media/project/${currentProject.value.id}/stream`;
});

function showToast(msg) {
  toastMessage.value = msg;
  setTimeout(() => {
    toastMessage.value = '';
  }, 3500);
}

function formatDuration(sec) {
  return formatTimeHHMMSS(sec);
}

// Fetch Initial Data
onMounted(async () => {
  try {
    const hwRes = await transcribeApi.getHardware();
    hardwareInfo.value = hwRes.data;
  } catch (err) {
    console.warn('Hardware info check:', err);
  }

  await loadProjects();
  if (projectList.value.length > 0) {
    await selectProject(projectList.value[0]);
  } else {
    isUploadModalOpen.value = true;
  }
});

async function loadProjects() {
  try {
    const res = await projectApi.list();
    projectList.value = res.data;
  } catch (err) {
    console.error('Failed to load projects:', err);
  }
}

async function selectProject(p) {
  currentProject.value = p;
  await loadSubtitles(p.id);
}

async function selectExistingProject(p) {
  await selectProject(p);
  isUploadModalOpen.value = false;
}

async function handleDeleteProject(projectId) {
  try {
    await projectApi.delete(projectId);
    showToast('Project berhasil dihapus');
    await loadProjects();
    if (currentProject.value?.id === projectId) {
      if (projectList.value.length > 0) {
        await selectProject(projectList.value[0]);
      } else {
        currentProject.value = null;
        subtitles.value = [];
        isUploadModalOpen.value = true;
      }
    }
  } catch (err) {
    alert(`Gagal menghapus project: ${err.response?.data?.detail || err.message}`);
  }
}

async function loadSubtitles(projectId) {
  try {
    const res = await subtitleApi.list(projectId);
    subtitles.value = res.data;
  } catch (err) {
    console.error('Failed to load subtitles:', err);
  }
}

function onVideoTimeUpdate(time) {
  currentTime.value = time;
}

function jumpToTime(time) {
  seekTarget.value = time;
}

// Native Tauri File Picker Handler (Zero-copy, Instant)
async function handleNativeFileSelect(nativeFilePath) {
  try {
    const res = await projectApi.registerLocal(nativeFilePath);
    currentProject.value = res.data;
    await loadProjects();
    await loadSubtitles(res.data.id);
    isUploadModalOpen.value = false;
    showToast('Video lokal berhasil dimuat (Instan tanpa upload)!');
    isTranscribeModalOpen.value = true;
  } catch (err) {
    alert(`Gagal memuat video: ${err.response?.data?.detail || err.message}`);
  }
}

// Upload Video Handler
async function handleVideoUpload(file) {
  isUploading.value = true;
  uploadProgress.value = 0;

  const formData = new FormData();
  formData.append('file', file);
  formData.append('name', file.name.replace(/\.[^/.]+$/, ''));

  try {
    const res = await projectApi.uploadVideo(formData, (evt) => {
      if (evt.total) {
        uploadProgress.value = Math.round((evt.loaded * 100) / evt.total);
      }
    });

    currentProject.value = res.data;
    await loadProjects();
    await loadSubtitles(res.data.id);
    isUploadModalOpen.value = false;
    showToast('Video berhasil diimpor!');
    
    // Suggest auto caption immediately
    isTranscribeModalOpen.value = true;
  } catch (err) {
    alert(`Upload gagal: ${err.response?.data?.detail || err.message}`);
  } finally {
    isUploading.value = false;
  }
}

// Transcription Handler with Server-Sent Events (SSE)
async function handleStartTranscribe({ model, language }) {
  if (!currentProject.value) return;
  isTranscribing.value = true;
  transcribeProgress.value = 5;
  transcribeStatus.value = 'Mengekstrak audio WAV...';
  latestSegmentText.value = '';

  const projectId = currentProject.value.id;

  // 1. Listen to SSE endpoint
  const eventSource = new EventSource(`/api/transcribe/events/${projectId}`);

  eventSource.addEventListener('progress', (e) => {
    try {
      const data = JSON.parse(e.data);
      if (data.progress !== undefined) {
        transcribeProgress.value = data.progress;
      }
      if (data.message) {
        transcribeStatus.value = data.message;
      }
      if (data.current_segment) {
        latestSegmentText.value = data.current_segment.text;
        transcribeStatus.value = `Menemukan teks (#${data.current_segment.sequence})...`;
      }

      if (data.status === 'completed') {
        eventSource.close();
        isTranscribing.value = false;
        isTranscribeModalOpen.value = false;
        loadSubtitles(projectId);
        showToast('Transkripsi Bahasa Indonesia selesai!');
      } else if (data.status === 'error') {
        eventSource.close();
        isTranscribing.value = false;
        alert(data.message || 'Terjadi kesalahan saat transkripsi.');
      }
    } catch (err) {
      console.error('SSE parse error:', err);
    }
  });

  eventSource.onerror = (err) => {
    console.error('SSE Error:', err);
  };

  // 2. Start transcription request
  try {
    await transcribeApi.start(projectId, model, language);
  } catch (err) {
    eventSource.close();
    isTranscribing.value = false;
    alert(`Gagal memulai transkripsi: ${err.response?.data?.detail || err.message}`);
  }
}

// Subtitle CRUD Operations
async function updateSubtitle(updatedData) {
  try {
    const res = await subtitleApi.update(updatedData.id, {
      text: updatedData.text,
      start_time: updatedData.start_time,
      end_time: updatedData.end_time,
    });
    // Update local state including newly synced words
    const item = subtitles.value.find((s) => s.id === updatedData.id);
    if (item && res.data) {
      item.text = res.data.text;
      item.start_time = res.data.start_time;
      item.end_time = res.data.end_time;
      item.words = res.data.words || [];
      item.words_json = res.data.words_json;
    }
  } catch (err) {
    console.error('Update subtitle failed:', err);
  }
}

async function addSubtitle() {
  if (!currentProject.value) return;
  const now = Math.round(currentTime.value * 1000) / 1000;
  try {
    await subtitleApi.create(currentProject.value.id, {
      startTime: now,
      endTime: now + 2.0,
      text: 'Teks subtitle baru',
    });
    await loadSubtitles(currentProject.value.id);
    showToast(`Baris subtitle ditambahkan pada posisi ${now}s`);
  } catch (err) {
    alert(`Gagal menambah baris: ${err.message}`);
  }
}

async function handleInsertAfter(item) {
  if (!currentProject.value) return;
  const startT = item.end_time;
  const endT = Math.round((item.end_time + 2.0) * 1000) / 1000;
  try {
    await subtitleApi.create(currentProject.value.id, {
      startTime: startT,
      endTime: endT,
      text: 'Teks subtitle baru',
      insertAfterId: item.id,
    });
    await loadSubtitles(currentProject.value.id);
    showToast(`Baris baru disisipkan setelah #${item.sequence}`);
  } catch (err) {
    alert(`Gagal menyisipkan baris: ${err.message}`);
  }
}

async function handleReorderSubtitles({ from, to }) {
  if (!currentProject.value) return;
  const list = [...subtitles.value];
  const [moved] = list.splice(from, 1);
  list.splice(to, 0, moved);
  list.forEach((s, idx) => {
    s.sequence = idx + 1;
  });
  subtitles.value = list;

  try {
    const ids = list.map((s) => s.id);
    await subtitleApi.reorder(currentProject.value.id, ids);
    showToast('Urutan subtitle berhasil diperbarui');
  } catch (err) {
    console.error('Reorder error:', err);
    await loadSubtitles(currentProject.value.id);
  }
}

async function handleMoveSubtitle({ item, direction }) {
  const idx = subtitles.value.findIndex((s) => s.id === item.id);
  if (idx === -1) return;
  const targetIdx = idx + direction;
  if (targetIdx < 0 || targetIdx >= subtitles.value.length) return;
  await handleReorderSubtitles({ from: idx, to: targetIdx });
}

async function handleSortByTime() {
  if (!currentProject.value) return;
  try {
    const res = await subtitleApi.sortByTime(currentProject.value.id);
    subtitles.value = res.data;
    showToast('Subtitle berhasil diurutkan berdasarkan waktu!');
  } catch (err) {
    alert(`Gagal mengurutkan: ${err.message}`);
  }
}

async function deleteSubtitle(item) {
  try {
    await subtitleApi.delete(item.id);
    await loadSubtitles(currentProject.value.id);
    showToast('Baris subtitle dihapus');
  } catch (err) {
    alert(`Gagal menghapus: ${err.message}`);
  }
}

function openSplitModal(item) {
  splitTargetItem.value = item;
  isSplitModalOpen.value = true;
}

async function handleConfirmSplit(payload) {
  try {
    await subtitleApi.split(currentProject.value.id, payload);
    await loadSubtitles(currentProject.value.id);
    isSplitModalOpen.value = false;
    showToast('Subtitle berhasil dipisahkan');
  } catch (err) {
    alert(`Gagal memisahkan subtitle: ${err.message}`);
  }
}

async function mergeSubtitleDown(item) {
  const idx = subtitles.value.findIndex((s) => s.id === item.id);
  if (idx === -1 || idx >= subtitles.value.length - 1) return;
  const nextItem = subtitles.value[idx + 1];

  try {
    await subtitleApi.merge(currentProject.value.id, {
      subtitle_id_1: item.id,
      subtitle_id_2: nextItem.id,
    });
    await loadSubtitles(currentProject.value.id);
    showToast('Subtitle berhasil digabungkan');
  } catch (err) {
    alert(`Gagal menggabungkan: ${err.message}`);
  }
}

async function resegmentSubtitles({ maxWords, maxChars }) {
  if (!currentProject.value) return;
  try {
    await subtitleApi.resegment(currentProject.value.id, {
      max_words: maxWords,
      max_chars: maxChars,
    });
    await loadSubtitles(currentProject.value.id);
    showToast(`Berhasil dirapikan (Maks ${maxWords} kata/baris)`);
  } catch (err) {
    alert(`Gagal merapikan baris: ${err.response?.data?.detail || err.message}`);
  }
}
</script>

<template>
  <div v-if="isOpen" class="modal modal-open">
    <div class="modal-box bg-[#11131a] border border-[#212534] text-slate-200 max-w-lg shadow-2xl rounded-2xl p-5">
      <!-- Modal Header -->
      <div class="flex items-center justify-between pb-3 border-b border-[#1d212c]">
        <div class="flex items-center gap-2">
          <div class="w-2 h-2 rounded-full bg-[#ffb800]"></div>
          <h3 class="font-bold text-sm tracking-wide text-white uppercase">
            Buka Video Studio
          </h3>
        </div>
        <button
          v-if="!isUploading"
          class="w-6 h-6 rounded-md bg-[#161822] hover:bg-[#202534] text-slate-400 hover:text-white flex items-center justify-center transition-colors cursor-pointer"
          @click="$emit('close')"
        >
          ✕
        </button>
      </div>

      <div class="flex flex-col gap-4 my-4">
        <!-- Tactile Dropzone -->
        <div
          class="border-2 border-dashed rounded-xl p-6 flex flex-col items-center justify-center text-center cursor-pointer transition-all relative overflow-hidden"
          :class="isDragging ? 'border-[#ffb800] bg-[#ffb800]/5' : 'border-[#262c3e] bg-[#0c0e14] hover:border-[#38415a]'"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="onDrop"
          @click="triggerFileInput"
        >
          <input
            ref="fileInputRef"
            type="file"
            accept="video/mp4,video/quicktime,video/x-matroska,video/webm"
            class="hidden"
            @change="onFileSelected"
          />

          <div class="w-12 h-12 rounded-xl bg-[#161924] border border-[#262c3e] text-[#ffb800] flex items-center justify-center mb-2.5 shadow-inner">
            <Film class="w-6 h-6" />
          </div>

          <p class="font-bold text-slate-200 text-xs">
            Tarik & Lepas Video ke sini atau <span class="text-[#ffb800] underline font-extrabold">Pilih File</span>
          </p>
          <p class="text-[10px] font-mono text-slate-500 mt-1 uppercase">
            MP4 • MOV • MKV • WebM (Zero-Copy Lokal)
          </p>
        </div>

        <!-- Selected File Preview & Upload Progress -->
        <div v-if="selectedFile" class="flex flex-col gap-2 p-2.5 bg-[#0a0c10] rounded-lg border border-[#1e222f]">
          <div class="flex items-center justify-between text-xs">
            <span class="font-semibold text-slate-200 truncate max-w-xs">{{ selectedFile.name }}</span>
            <span class="font-mono text-[10px] text-slate-400 font-bold">{{ formatFileSize(selectedFile.size) }}</span>
          </div>

          <div v-if="isUploading" class="flex flex-col gap-1">
            <div class="flex justify-between text-[10px] font-mono text-slate-400">
              <span>Mengimpor video...</span>
              <span class="text-[#ffb800] font-bold">{{ uploadPct }}%</span>
            </div>
            <progress class="progress progress-warning w-full h-1.5" :value="uploadPct" max="100"></progress>
          </div>
        </div>

        <!-- Existing Projects List -->
        <div v-if="existingProjects.length > 0" class="flex flex-col gap-2 pt-2 border-t border-[#1d212c]">
          <span class="text-[10px] font-mono uppercase text-slate-400 font-bold tracking-wider">Atau Pilih Project Sebelumnya:</span>
          <div class="max-h-36 overflow-y-auto flex flex-col gap-1.5 pr-1">
            <div
              v-for="p in existingProjects"
              :key="p.id"
              class="p-2 rounded-lg bg-[#0e1017] hover:bg-[#181a24] border border-[#1e222f] hover:border-[#ffb800]/50 flex items-center justify-between cursor-pointer transition-all group"
              @click="$emit('select-project', p)"
            >
              <div class="flex items-center gap-2 truncate">
                <Film class="w-3.5 h-3.5 text-[#ffb800] shrink-0" />
                <span class="text-xs text-slate-200 font-semibold truncate">{{ p.name }}</span>
              </div>
              <div class="flex items-center gap-2 shrink-0">
                <span class="text-[10px] text-slate-500 font-mono timecode">{{ formatDuration(p.duration) }}</span>
                <button
                  class="p-1 rounded text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                  title="Hapus project ini"
                  @click.stop="confirmDelete(p)"
                >
                  <Trash2 class="w-3 h-3" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Modal Actions -->
      <div class="flex items-center justify-end gap-2 border-t border-[#1d212c] pt-3">
        <button
          v-if="!isUploading"
          class="px-3 py-1.5 rounded-md bg-[#161822] hover:bg-[#202534] text-slate-400 hover:text-white text-xs font-semibold cursor-pointer transition-colors"
          @click="$emit('close')"
        >
          Batal
        </button>
        <button
          v-if="selectedFile && !isUploading"
          class="studio-btn-primary px-5 py-1.5 rounded-md text-xs font-black uppercase tracking-wider cursor-pointer"
          @click="startUpload"
        >
          Mulai Edit
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { Film, Trash2 } from '@lucide/vue';
import { formatTimeHHMMSS } from '../../utils/timeFormatter.js';

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  existingProjects: {
    type: Array,
    default: () => [],
  },
  isUploading: {
    type: Boolean,
    default: false,
  },
  uploadPct: {
    type: Number,
    default: 0,
  },
});

const emit = defineEmits(['close', 'upload', 'select-project', 'delete-project', 'select-native-path']);

function confirmDelete(project) {
  if (confirm(`Apakah Anda yakin ingin menghapus project "${project.name}" beserta videonya?`)) {
    emit('delete-project', project.id);
  }
}

const isDragging = ref(false);
const fileInputRef = ref(null);
const selectedFile = ref(null);
const isOpeningDialog = ref(false);

async function triggerFileInput() {
  if (isOpeningDialog.value) return;
  isOpeningDialog.value = true;

  try {
    // 1. PyWebView Native Desktop Support
    if (typeof window !== 'undefined' && window.pywebview?.api?.open_file_dialog) {
      try {
        const selected = await window.pywebview.api.open_file_dialog();
        if (selected) {
          emit('select-native-path', selected);
          return;
        }
      } catch (err) {
        console.warn('PyWebView file dialog fallback:', err);
      }
    }

    // 2. Tauri Native Desktop Support
    const isTauri = typeof window !== 'undefined' && ('__TAURI_INTERNALS__' in window || '__TAURI__' in window);
    if (isTauri) {
      try {
        const { open } = await import('@tauri-apps/plugin-dialog');
        const selected = await open({
          multiple: false,
          filters: [
            {
              name: 'Video',
              extensions: ['mp4', 'mov', 'mkv', 'webm', 'avi'],
            },
          ],
        });
        if (selected) {
          emit('select-native-path', selected);
          return;
        }
      } catch (err) {
        console.warn('Tauri native dialog fallback:', err);
      }
    }

    fileInputRef.value?.click();
  } finally {
    setTimeout(() => {
      isOpeningDialog.value = false;
    }, 600);
  }
}

function onFileSelected(e) {
  const file = e.target.files?.[0];
  if (file) selectedFile.value = file;
}

function onDrop(e) {
  isDragging.value = false;
  const file = e.dataTransfer.files?.[0];
  if (file) selectedFile.value = file;
}

function startUpload() {
  if (selectedFile.value) {
    emit('upload', selectedFile.value);
  }
}

function formatFileSize(bytes) {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  while (bytes >= 1024 && i < units.length - 1) {
    bytes /= 1024;
    i++;
  }
  return `${bytes.toFixed(1)} ${units[i]}`;
}

function formatDuration(sec) {
  return formatTimeHHMMSS(sec);
}
</script>

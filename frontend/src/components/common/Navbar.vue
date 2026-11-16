<template>
  <header class="h-14 bg-[#0e1015] border-b border-[#1c202a] px-4 flex items-center justify-between sticky top-0 z-40 select-none">
    <!-- Left: Brand & Project Info -->
    <div class="flex items-center gap-3 min-w-0">
      <!-- Studio Logo -->
      <div
        class="flex items-center gap-2.5 cursor-pointer group shrink-0"
        @click="$emit('go-home')"
        title="Kembali ke Beranda Studio"
      >
        <div class="w-8 h-8 rounded-lg bg-[#181a22] border border-[#2b3040] group-hover:border-[#ffb800]/60 flex items-center justify-center transition-all shadow-inner">
          <div class="relative flex items-center justify-center">
            <span class="w-2 h-2 rounded-full bg-[#ffb800] animate-ping absolute opacity-40"></span>
            <span class="w-2.5 h-2.5 rounded-full bg-[#ffb800]"></span>
          </div>
        </div>
        <div class="flex items-baseline gap-1.5">
          <span class="text-sm font-black tracking-tight text-white group-hover:text-[#ffb800] transition-colors">
            INDO<span class="text-[#ffb800]">CAPTION</span>
          </span>
          <span class="text-[10px] font-mono font-bold tracking-widest text-slate-500 uppercase px-1.5 py-0.5 rounded bg-[#161821] border border-[#242835]">
            STUDIO
          </span>
        </div>
      </div>

      <!-- Current Project Breadcrumb / HUD -->
      <div v-if="project" class="hidden md:flex items-center gap-2 pl-3 border-l border-[#1f232e] min-w-0">
        <div class="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#14161f] border border-[#232734] max-w-sm">
          <Film class="w-3.5 h-3.5 text-[#ffb800] shrink-0" />
          <span class="text-xs font-semibold text-slate-200 truncate max-w-[200px]" :title="project.name">
            {{ project.name }}
          </span>
          <span class="text-[11px] timecode text-slate-400 font-bold px-1.5 py-0.2 rounded bg-[#0b0c10] border border-[#1d202b] ml-1">
            {{ formatDuration(project.duration) }}
          </span>
        </div>

        <button
          class="p-1.5 rounded-md text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/30 transition-all shrink-0"
          title="Hapus project saat ini"
          @click="confirmDeleteCurrent"
        >
          <Trash2 class="w-3.5 h-3.5" />
        </button>
      </div>
    </div>

    <!-- Right: Hardware Status & Action Controls -->
    <div class="flex items-center gap-2 shrink-0">
      <!-- Hardware Rackmount LED Capsule -->
      <div
        v-if="hardwareInfo"
        class="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded-md bg-[#13151c] border border-[#222633] text-[11px]"
        title="Hardware Akselerasi AI Lokal"
      >
        <span class="relative flex h-2 w-2">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
        </span>
        <span class="font-mono font-bold text-slate-300">
          {{ hardwareInfo.device === 'cuda' ? 'GPU ACCELERATED' : 'CPU CORE' }}
        </span>
        <span class="text-slate-600">|</span>
        <span class="font-mono text-[10px] text-slate-400 font-medium uppercase">
          {{ hardwareInfo.recommended_compute_type }}
        </span>
      </div>

      <!-- Action 1: Auto Caption AI -->
      <button
        v-if="project"
        class="studio-btn-primary px-3 py-1.5 rounded-md text-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
        @click="$emit('open-transcribe')"
        :disabled="isTranscribing"
      >
        <Sparkles class="w-3.5 h-3.5 text-black" />
        <span class="tracking-wide uppercase font-extrabold text-[11px]">Auto Caption</span>
      </button>

      <!-- Action 2: Export Studio -->
      <button
        v-if="project"
        class="studio-btn-ghost px-3 py-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 cursor-pointer hover:border-emerald-500/50 hover:text-emerald-300 transition-all"
        @click="$emit('open-export')"
      >
        <Download class="w-3.5 h-3.5 text-emerald-400" />
        <span class="text-[11px] font-bold">Export</span>
      </button>

      <!-- Action 3: Open / Switch Video -->
      <button
        class="studio-btn-ghost px-2.5 py-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 cursor-pointer"
        @click="$emit('open-import')"
      >
        <FolderOpen class="w-3.5 h-3.5 text-slate-400" />
        <span class="hidden sm:inline text-[11px]">Buka Video</span>
      </button>
    </div>
  </header>
</template>

<script setup>
import { Film, Sparkles, Download, FolderOpen, Trash2 } from '@lucide/vue';
import { formatTimeHHMMSS } from '../../utils/timeFormatter.js';

const props = defineProps({
  project: {
    type: Object,
    default: null,
  },
  hardwareInfo: {
    type: Object,
    default: null,
  },
  isTranscribing: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['go-home', 'open-import', 'open-transcribe', 'open-export', 'delete-current']);

function confirmDeleteCurrent() {
  if (confirm(`Hapus project "${props.project?.name}" beserta semua subtitlenya?`)) {
    emit('delete-current', props.project?.id);
  }
}

function formatDuration(sec) {
  return formatTimeHHMMSS(sec);
}
</script>

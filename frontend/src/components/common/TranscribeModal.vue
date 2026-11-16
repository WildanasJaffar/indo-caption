<template>
  <div v-if="isOpen" class="modal modal-open">
    <div class="modal-box bg-[#11131a] border border-[#212534] text-slate-200 max-w-lg shadow-2xl rounded-2xl p-5">
      <!-- Header -->
      <div class="flex items-center justify-between pb-3 border-b border-[#1d212c]">
        <div class="flex items-center gap-2">
          <div class="w-2 h-2 rounded-full bg-[#ffb800] animate-pulse"></div>
          <h3 class="font-bold text-sm tracking-wide text-white uppercase">
            Auto Caption Engine (Faster-Whisper)
          </h3>
        </div>
        <button
          v-if="!isTranscribing"
          class="w-6 h-6 rounded-md bg-[#161822] hover:bg-[#202534] text-slate-400 hover:text-white flex items-center justify-center transition-colors cursor-pointer"
          @click="$emit('close')"
        >
          ✕
        </button>
      </div>

      <!-- Settings Form when not transcribing -->
      <div v-if="!isTranscribing" class="flex flex-col gap-3.5 my-4 text-xs">
        <!-- Language Mode Selection -->
        <div class="flex flex-col gap-1.5">
          <span class="text-[10px] font-mono uppercase text-slate-400 font-bold tracking-wider">Mode Bahasa Video</span>
          <div class="grid grid-cols-2 gap-2">
            <button
              type="button"
              class="p-2.5 rounded-lg border text-left transition-all cursor-pointer flex flex-col gap-0.5"
              :class="selectedLanguage === 'id-en'
                ? 'bg-[#1b1912] border-[#ffb800] shadow-sm'
                : 'bg-[#0d0f15] border-[#1e222f] hover:border-[#2f3547]'"
              @click="selectedLanguage = 'id-en'"
            >
              <div class="flex items-center justify-between">
                <span class="font-bold text-slate-100 text-xs">🌐 Campuran (Indo + EN)</span>
                <span v-if="selectedLanguage === 'id-en'" class="w-2 h-2 rounded-full bg-[#ffb800]"></span>
              </div>
              <span class="text-[10px] text-slate-400">Untuk bahasa Jaksel & istilah produk/inggris</span>
            </button>

            <button
              type="button"
              class="p-2.5 rounded-lg border text-left transition-all cursor-pointer flex flex-col gap-0.5"
              :class="selectedLanguage === 'id'
                ? 'bg-[#1b1912] border-[#ffb800] shadow-sm'
                : 'bg-[#0d0f15] border-[#1e222f] hover:border-[#2f3547]'"
              @click="selectedLanguage = 'id'"
            >
              <div class="flex items-center justify-between">
                <span class="font-bold text-slate-100 text-xs">🇮🇩 Khusus Indonesia</span>
                <span v-if="selectedLanguage === 'id'" class="w-2 h-2 rounded-full bg-[#ffb800]"></span>
              </div>
              <span class="text-[10px] text-slate-400">Fokus 100% kosakata Bahasa Indonesia</span>
            </button>
          </div>
        </div>

        <!-- Model Selection Cards -->
        <div class="flex flex-col gap-1.5">
          <span class="text-[10px] font-mono uppercase text-slate-400 font-bold tracking-wider">Pilih Model AI Whisper</span>
          <div class="grid grid-cols-1 gap-1.5 max-h-56 overflow-y-auto pr-1">
            <div
              v-for="m in models"
              :key="m.id"
              class="p-2.5 rounded-lg border cursor-pointer transition-all flex items-center justify-between"
              :class="selectedModel === m.id
                ? 'bg-[#1b1912] border-[#ffb800] shadow-sm'
                : 'bg-[#0d0f15] border-[#1e222f] hover:border-[#2f3547]'"
              @click="selectedModel = m.id"
            >
              <div class="flex items-center gap-2.5">
                <div
                  class="w-3.5 h-3.5 rounded-full border flex items-center justify-center shrink-0"
                  :class="selectedModel === m.id ? 'border-[#ffb800] bg-[#ffb800]' : 'border-slate-600 bg-transparent'"
                >
                  <span v-if="selectedModel === m.id" class="w-1.5 h-1.5 rounded-full bg-black"></span>
                </div>
                <div>
                  <div class="flex items-center gap-1.5">
                    <span class="font-bold text-slate-200">{{ m.name }}</span>
                    <span v-if="m.badge" class="text-[9px] font-mono font-bold text-black px-1.5 py-0.2 rounded uppercase" :class="m.badgeClass || 'bg-[#ffb800]'">
                      {{ m.badge }}
                    </span>
                  </div>
                  <p class="text-[10px] text-slate-400 mt-0.5">{{ m.desc }}</p>
                </div>
              </div>
              <span class="text-[10px] font-mono text-slate-500 font-bold shrink-0 ml-2">{{ m.ram }}</span>
            </div>
          </div>
        </div>

        <!-- Word-level & Privacy Note -->
        <div class="flex items-center justify-between px-3 py-2 bg-[#090b0e] rounded-lg border border-[#1e222f] text-[10px] font-mono">
          <span class="text-slate-400">Word Timestamps: <strong class="text-emerald-400">✓ Presisi Kata (CapCut)</strong></span>
          <span class="text-slate-500">🔒 100% Offline</span>
        </div>
      </div>

      <!-- Transcription Progress View with Soundwave Visualizer -->
      <div v-else class="flex flex-col items-center py-6 gap-4 text-center">
        <!-- Visual Soundwave Animation -->
        <div class="flex items-end justify-center gap-1.5 h-12">
          <span class="w-1.5 bg-[#ffb800] rounded-full animate-bounce [animation-delay:0.1s] h-8"></span>
          <span class="w-1.5 bg-[#ffb800] rounded-full animate-bounce [animation-delay:0.3s] h-12"></span>
          <span class="w-1.5 bg-[#ffb800] rounded-full animate-bounce [animation-delay:0.2s] h-6"></span>
          <span class="w-1.5 bg-[#ffb800] rounded-full animate-bounce [animation-delay:0.4s] h-10"></span>
          <span class="w-1.5 bg-[#ffb800] rounded-full animate-bounce [animation-delay:0.15s] h-7"></span>
        </div>

        <div class="w-full flex flex-col gap-2">
          <div class="flex justify-between text-xs text-slate-300 font-mono">
            <span>{{ progressStatus }}</span>
            <span class="font-bold text-[#ffb800]">{{ Math.round(progressPct) }}%</span>
          </div>
          <progress class="progress progress-warning w-full h-2" :value="progressPct" max="100"></progress>
        </div>

        <div v-if="latestSegmentText" class="w-full text-left bg-[#090b0e] p-2.5 rounded-lg border border-[#1e222f]">
          <span class="text-[9px] font-mono text-slate-500 block uppercase mb-1">Teks Sedang Diproses:</span>
          <p class="text-xs text-slate-200 italic truncate font-medium">
            "{{ latestSegmentText }}"
          </p>
        </div>
      </div>

      <!-- Modal Footer -->
      <div class="flex items-center justify-end gap-2 border-t border-[#1d212c] pt-3">
        <button
          v-if="!isTranscribing"
          class="px-3 py-1.5 rounded-md bg-[#161822] hover:bg-[#202534] text-slate-400 hover:text-white text-xs font-semibold cursor-pointer transition-colors"
          @click="$emit('close')"
        >
          Batal
        </button>
        <button
          v-if="!isTranscribing"
          class="studio-btn-primary px-5 py-1.5 rounded-md text-xs font-black uppercase tracking-wider cursor-pointer"
          @click="startTranscribe"
        >
          Mulai AI Transkripsi
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  isTranscribing: {
    type: Boolean,
    default: false,
  },
  progressPct: {
    type: Number,
    default: 0,
  },
  progressStatus: {
    type: String,
    default: 'Menyiapkan transkripsi...',
  },
  latestSegmentText: {
    type: String,
    default: '',
  },
});

const emit = defineEmits(['close', 'start']);

const selectedModel = ref('small');
const selectedLanguage = ref('id-en');

const models = [
  {
    id: 'tiny',
    name: 'Tiny (Ultra Cepat)',
    desc: 'Paling ringan, cocok untuk tes kilat atau PC spek rendah',
    ram: '~400 MB',
    badge: null,
  },
  {
    id: 'base',
    name: 'Base (Cepat)',
    desc: 'Kecepatan tinggi dengan akurasi dasar',
    ram: '~600 MB',
    badge: null,
  },
  {
    id: 'small',
    name: 'Small (Cepat & Seimbang)',
    desc: 'Optimal untuk CPU standar & sudah terunduh lokal',
    ram: '~1.2 GB',
    badge: 'REKOMENDASI CPU',
    badgeClass: 'bg-[#ffb800]',
  },
  {
    id: 'medium',
    name: 'Medium (Akurat)',
    desc: 'Akurasi tinggi untuk audio agak berisik atau kosakata beragam',
    ram: '~2.8 GB',
    badge: null,
  },
  {
    id: 'large-v3-turbo',
    name: 'Large-v3-Turbo (Bilingual Terbaik)',
    desc: 'Akurasi paling tajam untuk campuran Indo + English & istilah modern',
    ram: '~2.5 GB',
    badge: 'TERBAIK INDO-EN',
    badgeClass: 'bg-emerald-400',
  },
];

function startTranscribe() {
  emit('start', {
    model: selectedModel.value,
    language: selectedLanguage.value,
  });
}
</script>

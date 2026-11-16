<template>
  <div class="flex flex-col h-full bg-[#0d0f14] rounded-xl border border-[#1f232e] overflow-hidden shadow-2xl relative select-none">
    <!-- Monitor Header Strip -->
    <div class="h-7 bg-[#12141a] border-b border-[#1c202a] px-3 flex items-center justify-between text-[10px] font-mono tracking-wider text-slate-400">
      <div class="flex items-center gap-2">
        <span class="w-1.5 h-1.5 rounded-full" :class="isPlaying ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'"></span>
        <span class="font-bold text-slate-300">{{ isPlaying ? 'PLAYING' : 'PAUSED' }}</span>
        <span class="text-slate-600">|</span>
        <span>PREVIEW MONITOR</span>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-slate-500">SPEED: {{ playbackRate }}x</span>
        <span class="text-slate-600">|</span>
        <span class="text-[#ffb800] font-bold timecode">{{ formatTimecode(currentTime) }}</span>
      </div>
    </div>

    <!-- Video Canvas Area -->
    <div
      ref="videoContainer"
      class="relative flex-1 bg-[#07080a] flex items-center justify-center overflow-hidden min-h-[280px]"
      @click="togglePlay"
    >
      <video
        ref="videoRef"
        :src="videoSrc"
        class="max-h-full max-w-full object-contain pointer-events-none"
        preload="metadata"
        @timeupdate="onTimeUpdate"
        @loadedmetadata="onLoadedMetadata"
        @play="isPlaying = true"
        @pause="isPlaying = false"
        @ended="isPlaying = false"
      />

      <!-- Subtitle Overlay -->
      <CaptionOverlay
        :current-text="activeSubtitleText"
        :current-words="activeSubtitleWords"
        :current-time="currentTime"
        :style-config="styleConfig"
      />

      <!-- Play Overlay Pill when paused -->
      <transition enter-active-class="transition duration-150 ease-out" enter-from-class="opacity-0 scale-90" enter-to-class="opacity-100 scale-100" leave-active-class="transition duration-100 ease-in" leave-from-class="opacity-100 scale-100" leave-to-class="opacity-0 scale-90">
        <div
          v-if="!isPlaying"
          class="absolute inset-0 flex items-center justify-center bg-black/30 hover:bg-black/40 transition-colors pointer-events-none"
        >
          <div class="w-14 h-14 rounded-full bg-[#ffb800] text-[#0c0e12] flex items-center justify-center shadow-xl shadow-[#ffb800]/20 pl-0.5 transform hover:scale-105 transition-transform">
            <Play class="w-7 h-7 fill-current" />
          </div>
        </div>
      </transition>
    </div>

    <!-- Studio Transport Control Deck -->
    <div class="bg-[#12141b] border-t border-[#1c202a] p-3 flex flex-col gap-2.5">
      <!-- Scrubber Timeline with Ruler -->
      <div class="flex flex-col gap-1">
        <div class="relative w-full flex items-center">
          <input
            type="range"
            min="0"
            :max="duration || 100"
            step="0.04"
            :value="currentTime"
            @input="onSeek"
            class="range range-xs w-full cursor-pointer studio-slider"
          />
        </div>
      </div>

      <!-- Controls Row -->
      <div class="flex items-center justify-between text-xs">
        <!-- Left: Transport Buttons & Timecode -->
        <div class="flex items-center gap-1.5">
          <!-- Play / Pause -->
          <button
            class="w-8 h-8 rounded-md bg-[#1a1d27] hover:bg-[#242938] border border-[#272c3d] text-slate-100 hover:text-[#ffb800] flex items-center justify-center transition-all cursor-pointer"
            @click.stop="togglePlay"
            :title="isPlaying ? 'Pause (Space)' : 'Play (Space)'"
          >
            <Pause v-if="isPlaying" class="w-4 h-4 fill-current" />
            <Play v-else class="w-4 h-4 fill-current" />
          </button>

          <!-- Step Back 1 Frame -->
          <button
            class="w-7 h-7 rounded-md bg-[#141720] hover:bg-[#1f2330] border border-[#222634] text-slate-400 hover:text-white flex items-center justify-center text-[10px] font-mono cursor-pointer"
            @click.stop="stepFrame(-1)"
            title="Mundur 1 Frame (Tombol J)"
          >
            ◀
          </button>

          <!-- Skip -2s -->
          <button
            class="w-7 h-7 rounded-md bg-[#141720] hover:bg-[#1f2330] border border-[#222634] text-slate-400 hover:text-white flex items-center justify-center cursor-pointer"
            @click.stop="skip(-2)"
            title="Mundur 2 detik (Panah Kiri)"
          >
            <RotateCcw class="w-3.5 h-3.5" />
          </button>

          <!-- Skip +2s -->
          <button
            class="w-7 h-7 rounded-md bg-[#141720] hover:bg-[#1f2330] border border-[#222634] text-slate-400 hover:text-white flex items-center justify-center cursor-pointer"
            @click.stop="skip(2)"
            title="Maju 2 detik (Panah Kanan)"
          >
            <RotateCw class="w-3.5 h-3.5" />
          </button>

          <!-- Step Forward 1 Frame -->
          <button
            class="w-7 h-7 rounded-md bg-[#141720] hover:bg-[#1f2330] border border-[#222634] text-slate-400 hover:text-white flex items-center justify-center text-[10px] font-mono cursor-pointer"
            @click.stop="stepFrame(1)"
            title="Maju 1 Frame (Tombol L)"
          >
            ▶
          </button>

          <!-- Digital Timecode Counter -->
          <div class="px-2 py-1 rounded-md bg-[#0a0c10] border border-[#1b1f2b] flex items-center gap-1.5 ml-1 timecode text-[11px]">
            <span class="text-[#ffb800] font-bold">{{ formatTimeHHMMSS(currentTime) }}</span>
            <span class="text-slate-600">/</span>
            <span class="text-slate-400">{{ formatTimeHHMMSS(duration) }}</span>
          </div>
        </div>

        <!-- Right: Speed Selector & Fullscreen -->
        <div class="flex items-center gap-2">
          <!-- Segmented Speed Pills -->
          <div class="flex items-center rounded-md bg-[#0a0c10] p-0.5 border border-[#1c202c]">
            <button
              v-for="rate in [0.75, 1, 1.25, 1.5]"
              :key="rate"
              class="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold transition-all"
              :class="playbackRate === rate ? 'bg-[#ffb800] text-black shadow-sm' : 'text-slate-400 hover:text-white'"
              @click.stop="setSpeed(rate)"
            >
              {{ rate }}x
            </button>
          </div>

          <!-- Mute Toggle -->
          <button
            class="w-7 h-7 rounded-md bg-[#141720] hover:bg-[#1f2330] border border-[#222634] text-slate-400 hover:text-white flex items-center justify-center cursor-pointer"
            @click.stop="toggleMute"
            :title="isMuted ? 'Unmute' : 'Mute'"
          >
            <VolumeX v-if="isMuted" class="w-3.5 h-3.5 text-rose-400" />
            <Volume2 v-else class="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { Play, Pause, RotateCcw, RotateCw, Volume2, VolumeX } from '@lucide/vue';
import CaptionOverlay from './CaptionOverlay.vue';
import { formatTimeHHMMSS } from '../../utils/timeFormatter.js';

const props = defineProps({
  videoSrc: {
    type: String,
    required: true,
  },
  subtitles: {
    type: Array,
    default: () => [],
  },
  styleConfig: {
    type: Object,
    required: true,
  },
  seekTarget: {
    type: Number,
    default: null,
  },
});

const emit = defineEmits(['time-update', 'duration-change']);

const videoRef = ref(null);
const videoContainer = ref(null);
const isPlaying = ref(false);
const currentTime = ref(0);
const duration = ref(0);
const playbackRate = ref(1);
const isMuted = ref(false);

const activeSubtitle = computed(() => {
  const t = currentTime.value;
  return props.subtitles.find((s) => t >= s.start_time && t <= s.end_time);
});

const activeSubtitleText = computed(() => activeSubtitle.value?.text || '');
const activeSubtitleWords = computed(() => activeSubtitle.value?.words || []);

function togglePlay() {
  if (!videoRef.value) return;
  if (videoRef.value.paused) {
    videoRef.value.play().catch(console.warn);
  } else {
    videoRef.value.pause();
  }
}

function onTimeUpdate() {
  if (!videoRef.value) return;
  currentTime.value = videoRef.value.currentTime;
  emit('time-update', currentTime.value);
}

function onLoadedMetadata() {
  if (!videoRef.value) return;
  duration.value = videoRef.value.duration;
  emit('duration-change', duration.value);
}

function onSeek(e) {
  const target = parseFloat(e.target.value);
  if (!videoRef.value) return;
  videoRef.value.currentTime = target;
  currentTime.value = target;
  emit('time-update', target);
}

function skip(seconds) {
  if (!videoRef.value) return;
  const newTime = Math.max(0, Math.min(duration.value, videoRef.value.currentTime + seconds));
  videoRef.value.currentTime = newTime;
}

function stepFrame(frames = 1) {
  if (!videoRef.value) return;
  const frameTime = 1 / 30; // standard 30fps
  const newTime = Math.max(0, Math.min(duration.value, videoRef.value.currentTime + (frames * frameTime)));
  videoRef.value.currentTime = newTime;
}

function setSpeed(rate) {
  playbackRate.value = rate;
  if (videoRef.value) videoRef.value.playbackRate = rate;
}

function toggleMute() {
  if (!videoRef.value) return;
  isMuted.value = !isMuted.value;
  videoRef.value.muted = isMuted.value;
}

function formatTimecode(sec) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  const ms = Math.floor((sec % 1) * 100);
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}.${String(ms).padStart(2, '0')}`;
}

watch(
  () => props.seekTarget,
  (val) => {
    if (val !== null && videoRef.value) {
      videoRef.value.currentTime = val;
    }
  }
);

function handleKeyDown(e) {
  if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) return;
  if (e.code === 'Space') {
    e.preventDefault();
    togglePlay();
  } else if (e.code === 'ArrowLeft') {
    e.preventDefault();
    skip(-2);
  } else if (e.code === 'ArrowRight') {
    e.preventDefault();
    skip(2);
  } else if (e.key === 'j' || e.key === 'J') {
    stepFrame(-1);
  } else if (e.key === 'l' || e.key === 'L') {
    stepFrame(1);
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown);
});
</script>

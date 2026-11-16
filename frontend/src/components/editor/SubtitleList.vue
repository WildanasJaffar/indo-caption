<template>
  <div class="flex flex-col h-full bg-[#111319] border border-[#1e222d] rounded-xl overflow-hidden shadow-2xl select-none">
    <!-- Studio Header & Tools Deck -->
    <div class="p-3 border-b border-[#1c202a] bg-[#14161f] flex flex-col gap-2.5">
      <!-- Row 1: Title, Count, Follow Toggle, Auto-sort, Add Button -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-2 h-2 rounded-full bg-[#ffb800]"></div>
          <h3 class="font-bold text-slate-100 text-xs tracking-wider uppercase">Daftar Subtitle</h3>
          <span class="text-[10px] font-mono font-bold text-slate-400 bg-[#0a0c10] px-2 py-0.5 rounded border border-[#1d202b]">
            {{ subtitles.length }} KLIP
          </span>
        </div>

        <div class="flex items-center gap-1.5">
          <!-- Follow Playhead Toggle -->
          <label class="cursor-pointer flex items-center gap-1 text-[11px] font-medium text-slate-400 hover:text-slate-200 transition-colors mr-1" title="Otomatis scroll mengikuti posisi video">
            <input type="checkbox" v-model="autoScroll" class="checkbox checkbox-xs rounded border-[#343b4f] checked:border-[#ffb800] checked:bg-[#ffb800]" />
            <span>Follow</span>
          </label>

          <!-- Auto-sort Chronologically Button -->
          <button
            class="px-2 py-1 rounded-md bg-[#141722] hover:bg-[#1f2434] border border-[#252b3d] text-slate-300 hover:text-[#ffb800] text-[11px] font-semibold flex items-center gap-1 cursor-pointer transition-all"
            @click="$emit('sort-by-time')"
            title="Urutkan semua baris subtitle secara kronologis berdasarkan waktu"
          >
            <ArrowUpDown class="w-3 h-3 text-amber-400" />
            <span class="hidden sm:inline">Urutkan Waktu</span>
          </button>

          <!-- Add Clip at Current Playhead Button -->
          <button
            class="px-2 py-1 rounded-md bg-[#1d212c] hover:bg-[#282d3d] border border-[#2b3142] text-slate-200 hover:text-white text-[11px] font-bold flex items-center gap-1 cursor-pointer transition-all"
            @click="$emit('add-subtitle')"
            title="Tambah baris baru pada posisi video saat ini"
          >
            <Plus class="w-3.5 h-3.5 text-[#ffb800]" />
            <span>Tambah</span>
          </button>
        </div>
      </div>

      <!-- Row 2: Viral Word Limit Segmented Control & Search -->
      <div class="flex items-center justify-between gap-2 pt-2 border-t border-[#1b1e28]">
        <!-- Word Density Selector (Segmented buttons) -->
        <div class="flex items-center gap-1.5 text-xs">
          <span class="text-[10px] font-mono text-slate-400 font-bold uppercase">Maks:</span>
          <div class="flex items-center bg-[#0a0c10] p-0.5 rounded-md border border-[#1d202b]">
            <button
              v-for="w in [3, 4, 5, 6]"
              :key="w"
              class="px-2 py-0.5 rounded text-[10px] font-mono font-bold transition-all cursor-pointer"
              :class="maxWords === w ? 'bg-[#ffb800] text-black shadow-sm' : 'text-slate-400 hover:text-white'"
              @click="maxWords = w"
            >
              {{ w }}k
            </button>
          </div>

          <button
            class="px-2 py-1 rounded-md bg-[#191c26] hover:bg-[#222634] border border-[#2a2f40] text-[#ffb800] hover:text-[#ffc53d] text-[10px] font-bold flex items-center gap-1 cursor-pointer transition-all ml-0.5"
            @click="$emit('resegment', { maxWords, maxChars: 26 })"
            title="Potong ulang kalimat panjang menjadi baris pendek ala TikTok"
          >
            <Sparkles class="w-3 h-3 text-[#ffb800]" />
            <span>Potong Ulang</span>
          </button>
        </div>

        <!-- Search Bar -->
        <div class="relative w-36">
          <Search class="w-3 h-3 absolute left-2 top-2 text-slate-500" />
          <input
            type="text"
            v-model="searchQuery"
            placeholder="Cari teks..."
            class="w-full bg-[#0a0c10] border border-[#1e222d] rounded-md pl-6 pr-2 py-1 text-slate-200 placeholder-slate-500 text-[11px] focus:outline-none focus:border-[#ffb800]/60 transition-colors"
          />
        </div>
      </div>
    </div>

    <!-- Subtitle Cards Scroll Area with Drag & Drop Reordering -->
    <div
      ref="listContainer"
      class="flex-1 overflow-y-auto p-2.5 flex flex-col gap-2"
    >
      <div v-if="filteredSubtitles.length === 0" class="flex-1 flex flex-col items-center justify-center p-8 text-center text-slate-500">
        <div class="w-12 h-12 rounded-xl bg-[#141720] border border-[#202534] flex items-center justify-center mb-3">
          <FileText class="w-6 h-6 text-slate-500" />
        </div>
        <p class="text-xs font-bold text-slate-400 uppercase tracking-wide">Belum Ada Subtitle</p>
        <p class="text-[11px] text-slate-500 max-w-xs mt-1 leading-relaxed">
          Gunakan tombol <strong class="text-[#ffb800]">Auto Caption</strong> di atas untuk membuat teks bahasa Indonesia otomatis dengan AI.
        </p>
      </div>

      <div
        v-for="(item, idx) in filteredSubtitles"
        :key="item.id || item.sequence"
        :id="`sub-item-${item.id}`"
        draggable="true"
        @dragstart="onDragStart(idx, $event)"
        @dragover.prevent="onDragOver(idx, $event)"
        @dragleave="onDragLeave(idx)"
        @drop="onDrop(idx)"
        @dragend="onDragEnd"
        class="transition-all duration-100 rounded-lg"
        :class="{
          'opacity-40 scale-[0.98]': draggedIndex === idx,
          'border-t-2 border-t-[#ffb800] pt-1': dragOverIndex === idx && draggedIndex !== idx
        }"
      >
        <SubtitleItem
          :item="item"
          :is-active="activeSubtitleId === item.id"
          :current-time="currentTime"
          :is-first="idx === 0"
          :is-last="idx === filteredSubtitles.length - 1"
          @jump="$emit('jump', $event)"
          @update="$emit('update-subtitle', $event)"
          @split="$emit('open-split', item)"
          @merge-down="$emit('merge-down', item)"
          @delete="$emit('delete-subtitle', item)"
          @move-up="$emit('move-subtitle', { item, direction: -1 })"
          @move-down="$emit('move-subtitle', { item, direction: 1 })"
          @insert-after="$emit('insert-after', item)"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue';
import { Plus, Sparkles, Search, FileText, ArrowUpDown } from '@lucide/vue';
import SubtitleItem from './SubtitleItem.vue';

const props = defineProps({
  subtitles: {
    type: Array,
    default: () => [],
  },
  currentTime: {
    type: Number,
    default: 0,
  },
});

const emit = defineEmits([
  'jump',
  'update-subtitle',
  'delete-subtitle',
  'add-subtitle',
  'open-split',
  'merge-down',
  'resegment',
  'move-subtitle',
  'reorder-indices',
  'sort-by-time',
  'insert-after',
]);

const autoScroll = ref(true);
const maxWords = ref(4);
const searchQuery = ref('');
const listContainer = ref(null);

// Drag & Drop Reordering State
const draggedIndex = ref(null);
const dragOverIndex = ref(null);

function onDragStart(idx, evt) {
  draggedIndex.value = idx;
  evt.dataTransfer.effectAllowed = 'move';
  evt.dataTransfer.setData('text/plain', idx.toString());
}

function onDragOver(idx) {
  dragOverIndex.value = idx;
}

function onDragLeave(idx) {
  if (dragOverIndex.value === idx) {
    dragOverIndex.value = null;
  }
}

function onDrop(targetIdx) {
  if (draggedIndex.value === null || draggedIndex.value === targetIdx) {
    draggedIndex.value = null;
    dragOverIndex.value = null;
    return;
  }

  const from = draggedIndex.value;
  const to = targetIdx;
  draggedIndex.value = null;
  dragOverIndex.value = null;

  emit('reorder-indices', { from, to });
}

function onDragEnd() {
  draggedIndex.value = null;
  dragOverIndex.value = null;
}

const activeSubtitleId = computed(() => {
  const t = props.currentTime;
  const current = props.subtitles.find((s) => t >= s.start_time && t <= s.end_time);
  return current ? current.id : null;
});

const filteredSubtitles = computed(() => {
  if (!searchQuery.value.trim()) return props.subtitles;
  const q = searchQuery.value.toLowerCase();
  return props.subtitles.filter((s) => s.text.toLowerCase().includes(q));
});

// Auto-scroll when active clip changes
watch(activeSubtitleId, async (newId) => {
  if (!autoScroll.value || !newId || !listContainer.value) return;
  await nextTick();
  const el = document.getElementById(`sub-item-${newId}`);
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
});
</script>

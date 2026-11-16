<template>
  <div
    class="p-2.5 rounded-lg border transition-all duration-150 flex flex-col gap-2 relative group"
    :class="isActive
      ? 'bg-[#1a1711] border-[#ffb800] shadow-[0_0_12px_rgba(255,184,0,0.12)]'
      : 'bg-[#151720] border-[#202431] hover:border-[#2f3547]'"
    @click="$emit('select', item)"
  >
    <!-- Top Row: Sequence, Duration, Timings, Actions -->
    <div class="flex items-center justify-between gap-2 text-xs">
      <div class="flex items-center gap-1.5">
        <!-- Drag Handle Indicator -->
        <span
          class="cursor-grab active:cursor-grabbing text-slate-500 hover:text-[#ffb800] transition-colors p-0.5"
          title="Tarik & letakkan kartu ini untuk mengatur urutan"
        >
          <GripVertical class="w-3.5 h-3.5" />
        </span>

        <!-- Sequence Badge -->
        <span
          class="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded"
          :class="isActive ? 'bg-[#ffb800] text-black' : 'bg-[#0b0c10] text-slate-400 border border-[#1e222f]'"
        >
          #{{ item.sequence }}
        </span>

        <!-- Jump to time button -->
        <button
          class="w-5 h-5 rounded bg-[#101218] hover:bg-[#1f2330] border border-[#232735] text-slate-400 hover:text-[#ffb800] flex items-center justify-center transition-colors cursor-pointer"
          @click.stop="$emit('jump', item.start_time)"
          title="Putar dari detik ini"
        >
          <Play class="w-2.5 h-2.5 fill-current" />
        </button>

        <!-- Precision Timecode Deck -->
        <div class="flex items-center gap-1 timecode text-[11px] text-slate-300">
          <input
            type="text"
            v-model="startDisplay"
            @focus="isTimeFocused = true"
            @blur="commitTimeChange"
            @keydown.enter="commitTimeChange"
            class="w-16 px-1 py-0.5 text-center bg-[#090b0e] border border-[#232735] focus:border-[#ffb800] rounded text-slate-200 timecode text-[10px] focus:outline-none"
            title="Waktu mulai (mm:ss.mmm)"
          />
          <span class="text-slate-600 font-bold">→</span>
          <input
            type="text"
            v-model="endDisplay"
            @focus="isTimeFocused = true"
            @blur="commitTimeChange"
            @keydown.enter="commitTimeChange"
            class="w-16 px-1 py-0.5 text-center bg-[#090b0e] border border-[#232735] focus:border-[#ffb800] rounded text-slate-200 timecode text-[10px] focus:outline-none"
            title="Waktu selesai (mm:ss.mmm)"
          />
        </div>

        <!-- Duration pill -->
        <span class="text-[9px] font-mono font-medium text-slate-500 px-1 py-0.5 rounded bg-[#090b0e] border border-[#1a1c24] hidden sm:inline">
          {{ clipDuration }}s
        </span>
      </div>

      <!-- Action Buttons Deck -->
      <div class="flex items-center gap-0.5 opacity-80 group-hover:opacity-100 transition-opacity">
        <!-- Reorder: Move Up -->
        <button
          class="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 disabled:opacity-20 disabled:hover:bg-transparent transition-colors cursor-pointer"
          @click.stop="$emit('move-up', item)"
          :disabled="isFirst"
          title="Pindah ke atas (geser urutan lebih awal)"
        >
          <ChevronUp class="w-3.5 h-3.5" />
        </button>

        <!-- Reorder: Move Down -->
        <button
          class="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 disabled:opacity-20 disabled:hover:bg-transparent transition-colors cursor-pointer"
          @click.stop="$emit('move-down', item)"
          :disabled="isLast"
          title="Pindah ke bawah (geser urutan setelahnya)"
        >
          <ChevronDown class="w-3.5 h-3.5" />
        </button>

        <div class="w-px h-3 bg-[#242938] mx-0.5"></div>

        <!-- Insert After Button -->
        <button
          class="p-1 rounded text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10 transition-colors cursor-pointer"
          @click.stop="$emit('insert-after', item)"
          title="Sisipkan baris baru setelah klip ini"
        >
          <PlusCircle class="w-3 h-3" />
        </button>

        <!-- Split Button -->
        <button
          class="p-1 rounded text-slate-400 hover:text-[#ffb800] hover:bg-[#ffb800]/10 transition-colors cursor-pointer"
          @click.stop="$emit('split', item)"
          title="Pisah klip ini jadi dua"
        >
          <Scissors class="w-3 h-3" />
        </button>

        <!-- Merge Down Button (if not last) -->
        <button
          v-if="!isLast"
          class="p-1 rounded text-slate-400 hover:text-indigo-300 hover:bg-indigo-500/10 transition-colors cursor-pointer"
          @click.stop="$emit('merge-down', item)"
          title="Gabungkan dengan baris di bawahnya"
        >
          <ArrowDownToLine class="w-3 h-3" />
        </button>

        <!-- Delete Button -->
        <button
          class="p-1 rounded text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors cursor-pointer"
          @click.stop="$emit('delete', item)"
          title="Hapus baris ini"
        >
          <Trash2 class="w-3 h-3" />
        </button>
      </div>
    </div>

    <!-- Live Word Karaoke Chips (when active and words present) -->
    <div v-if="isActive && item.words && item.words.length > 0" class="flex flex-wrap gap-1 px-1 py-0.5">
      <span
        v-for="(w, idx) in item.words"
        :key="idx"
        class="text-[10px] font-semibold px-1.5 py-0.2 rounded transition-all duration-75"
        :class="isWordActive(w)
          ? 'bg-[#ffb800] text-black font-bold scale-105 shadow-sm'
          : 'bg-[#090b0e] text-slate-400 border border-[#1d202b]'"
      >
        {{ w.word }}
      </span>
    </div>

    <!-- Textarea for Caption Text -->
    <textarea
      ref="textareaRef"
      v-model="currentText"
      @focus="isFocused = true"
      @input="onTextInput"
      @blur="commitTextChange"
      @keydown.enter.ctrl="commitTextChange"
      rows="2"
      class="w-full bg-[#0a0c10] border border-[#1e222d] rounded-md p-2 text-slate-100 text-xs leading-relaxed focus:outline-none focus:border-[#ffb800]/70 resize-none transition-colors"
      placeholder="Tulis caption di sini..."
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue';
import {
  Play,
  Scissors,
  ArrowDownToLine,
  Trash2,
  GripVertical,
  ChevronUp,
  ChevronDown,
  PlusCircle,
} from '@lucide/vue';
import { formatTime, parseTime } from '../../utils/timeFormatter.js';

const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
  isActive: {
    type: Boolean,
    default: false,
  },
  currentTime: {
    type: Number,
    default: 0,
  },
  isFirst: {
    type: Boolean,
    default: false,
  },
  isLast: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits([
  'select',
  'jump',
  'update',
  'split',
  'merge-down',
  'delete',
  'move-up',
  'move-down',
  'insert-after',
]);

const isFocused = ref(false);
const isTimeFocused = ref(false);
let debounceTimer = null;

const currentText = ref(props.item.text);
const startDisplay = ref(formatTime(props.item.start_time));
const endDisplay = ref(formatTime(props.item.end_time));

const clipDuration = computed(() => {
  const diff = (props.item.end_time - props.item.start_time).toFixed(1);
  return Math.max(0, parseFloat(diff));
});

function isWordActive(w) {
  return props.currentTime >= w.start && props.currentTime <= w.end;
}

watch(
  () => props.item.text,
  (val) => {
    if (!isFocused.value) {
      currentText.value = val;
    }
  }
);

watch(
  () => props.item.start_time,
  (val) => {
    if (!isTimeFocused.value) {
      startDisplay.value = formatTime(val);
    }
  }
);

watch(
  () => props.item.end_time,
  (val) => {
    if (!isTimeFocused.value) {
      endDisplay.value = formatTime(val);
    }
  }
);

function onTextInput() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    commitTextChange();
  }, 400);
}

function commitTextChange() {
  clearTimeout(debounceTimer);
  isFocused.value = false;
  const trimmed = currentText.value.trim();
  if (trimmed !== props.item.text) {
    emit('update', {
      ...props.item,
      text: trimmed,
    });
  }
}

function commitTimeChange() {
  isTimeFocused.value = false;
  const newStart = parseTime(startDisplay.value);
  const newEnd = parseTime(endDisplay.value);

  if (isNaN(newStart) || isNaN(newEnd) || newStart >= newEnd) {
    startDisplay.value = formatTime(props.item.start_time);
    endDisplay.value = formatTime(props.item.end_time);
    return;
  }

  emit('update', {
    ...props.item,
    start_time: newStart,
    end_time: newEnd,
  });
}

onBeforeUnmount(() => {
  clearTimeout(debounceTimer);
});
</script>

<template>
  <div v-if="isOpen" class="modal modal-open">
    <div class="modal-box bg-[#11131a] border border-[#212534] text-slate-200 max-w-md shadow-2xl rounded-2xl p-5">
      <div class="flex items-center justify-between pb-3 border-b border-[#1d212c]">
        <div class="flex items-center gap-2">
          <Scissors class="w-4 h-4 text-[#ffb800]" />
          <h3 class="font-bold text-sm tracking-wide text-white uppercase">
            Pisahkan Klip (#{{ item?.sequence }})
          </h3>
        </div>
        <button
          class="w-6 h-6 rounded-md bg-[#161822] hover:bg-[#202534] text-slate-400 hover:text-white flex items-center justify-center transition-colors cursor-pointer"
          @click="$emit('close')"
        >
          ✕
        </button>
      </div>

      <p class="text-[11px] text-slate-400 mt-2">
        Bagi subtitle ini menjadi dua baris dengan timing masing-masing.
      </p>

      <div class="flex flex-col gap-3 my-4">
        <!-- Part 1 -->
        <div class="flex flex-col gap-1">
          <label class="text-[10px] font-mono uppercase text-slate-400 font-bold tracking-wider">Bagian 1 (Teks)</label>
          <input
            type="text"
            v-model="part1Text"
            class="w-full bg-[#090b0e] border border-[#212532] text-slate-100 text-xs rounded-md p-2 focus:outline-none focus:border-[#ffb800]"
          />
        </div>

        <!-- Split Time -->
        <div class="flex flex-col gap-1.5 p-2.5 rounded-lg bg-[#0c0e14] border border-[#1e222f]">
          <div class="flex justify-between items-center text-[10px] font-mono text-slate-400 font-bold uppercase">
            <span>Waktu Pisah</span>
            <span class="text-[#ffb800] timecode font-bold">{{ formatTime(splitTime) }}</span>
          </div>
          <input
            type="range"
            :min="item?.start_time || 0"
            :max="item?.end_time || 1"
            step="0.05"
            v-model.number="splitTime"
            class="range range-xs studio-slider cursor-pointer"
          />
        </div>

        <!-- Part 2 -->
        <div class="flex flex-col gap-1">
          <label class="text-[10px] font-mono uppercase text-slate-400 font-bold tracking-wider">Bagian 2 (Teks)</label>
          <input
            type="text"
            v-model="part2Text"
            class="w-full bg-[#090b0e] border border-[#212532] text-slate-100 text-xs rounded-md p-2 focus:outline-none focus:border-[#ffb800]"
          />
        </div>
      </div>

      <div class="flex items-center justify-end gap-2 border-t border-[#1d212c] pt-3">
        <button
          class="px-3 py-1.5 rounded-md bg-[#161822] hover:bg-[#202534] text-slate-400 hover:text-white text-xs font-semibold cursor-pointer transition-colors"
          @click="$emit('close')"
        >
          Batal
        </button>
        <button
          class="studio-btn-primary px-5 py-1.5 rounded-md text-xs font-black uppercase tracking-wider cursor-pointer disabled:opacity-50"
          @click="confirmSplit"
          :disabled="!part1Text.trim() || !part2Text.trim()"
        >
          Pisahkan Sekarang
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { Scissors } from '@lucide/vue';
import { formatTime } from '../../utils/timeFormatter.js';

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  item: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(['close', 'confirm']);

const part1Text = ref('');
const part2Text = ref('');
const splitTime = ref(0);

watch(
  () => props.item,
  (newItem) => {
    if (!newItem) return;
    const words = newItem.text.trim().split(/\s+/);
    const mid = Math.ceil(words.length / 2);
    part1Text.value = words.slice(0, mid).join(' ');
    part2Text.value = words.slice(mid).join(' ');

    const duration = newItem.end_time - newItem.start_time;
    splitTime.value = round3(newItem.start_time + duration / 2);
  },
  { immediate: true }
);

function round3(n) {
  return Math.round(n * 1000) / 1000;
}

function confirmSplit() {
  if (!part1Text.value.trim() || !part2Text.value.trim()) return;
  emit('confirm', {
    subtitleId: props.item.id,
    splitTime: splitTime.value,
    part1Text: part1Text.value.trim(),
    part2Text: part2Text.value.trim(),
  });
}
</script>

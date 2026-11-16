<template>
  <div class="flex flex-col h-full bg-[#111319] border border-[#1e222d] rounded-xl overflow-hidden shadow-2xl p-3.5 gap-3.5 select-none text-xs">
    <!-- Header -->
    <div class="flex items-center justify-between border-b border-[#1c202a] pb-2.5">
      <div class="flex items-center gap-2">
        <div class="w-2 h-2 rounded-full bg-[#ffb800]"></div>
        <h3 class="font-bold text-slate-100 text-xs tracking-wider uppercase">Styling Caption</h3>
      </div>
      <button
        class="text-[11px] font-medium text-slate-400 hover:text-white px-2 py-0.5 rounded bg-[#171a24] hover:bg-[#202534] border border-[#232735] transition-all cursor-pointer"
        @click="resetToDefault"
      >
        Reset Default
      </button>
    </div>

    <!-- Social Presets -->
    <div class="flex flex-col gap-1.5">
      <span class="text-[10px] font-mono uppercase text-slate-400 font-bold tracking-wider">Preset Media Sosial</span>
      <div class="grid grid-cols-3 gap-1.5">
        <button
          v-for="p in presets"
          :key="p.id"
          class="flex flex-col items-center justify-center py-2 px-1 rounded-lg border transition-all text-center cursor-pointer"
          :class="activePresetId === p.id
            ? 'bg-[#1e1b12] border-[#ffb800] text-[#ffb800] shadow-sm'
            : 'bg-[#151720] border-[#222634] text-slate-300 hover:border-[#333a4f]'"
          @click="applyPreset(p)"
        >
          <span class="font-bold text-[11px] truncate w-full">{{ p.name }}</span>
          <span class="text-[9px] text-slate-500 truncate w-full mt-0.5">{{ p.sub }}</span>
        </button>
      </div>
    </div>

    <!-- Controls Body -->
    <div class="flex-1 overflow-y-auto pr-1 flex flex-col gap-3.5">
      <!-- Font Family -->
      <div class="flex flex-col gap-1.5">
        <label class="text-[10px] font-mono uppercase text-slate-400 font-bold tracking-wider">Jenis Font</label>
        <select
          v-model="modelValue.fontFamily"
          class="w-full bg-[#090b0e] border border-[#212532] text-slate-200 text-xs rounded-md p-2 focus:outline-none focus:border-[#ffb800]"
        >
          <option value="Poppins, sans-serif">Poppins (Rounded Viral)</option>
          <option value="Montserrat, sans-serif">Montserrat (Modern Bold)</option>
          <option value="Impact, sans-serif">Impact (Ultra TikTok)</option>
          <option value="Inter, sans-serif">Inter (Clean Minimal)</option>
          <option value="Roboto, sans-serif">Roboto (Standard)</option>
          <option value="Oswald, sans-serif">Oswald (Condensed)</option>
        </select>
      </div>

      <!-- Font Size & Case -->
      <div class="grid grid-cols-2 gap-2.5">
        <!-- Font Size -->
        <div class="flex flex-col gap-1.5">
          <div class="flex justify-between items-center text-[10px] font-mono text-slate-400 font-bold uppercase">
            <span>Ukuran</span>
            <span class="text-[#ffb800]">{{ modelValue.fontSize }}px</span>
          </div>
          <input
            type="range"
            min="18"
            max="60"
            v-model.number="modelValue.fontSize"
            class="range range-xs studio-slider cursor-pointer"
          />
        </div>

        <!-- Format Text -->
        <div class="flex flex-col gap-1.5">
          <span class="text-[10px] font-mono text-slate-400 font-bold uppercase">Format Huruf</span>
          <button
            class="py-1.5 px-2 rounded-md font-bold text-xs border transition-all cursor-pointer"
            :class="modelValue.textTransform === 'uppercase'
              ? 'bg-[#ffb800] border-[#ffb800] text-black font-extrabold'
              : 'bg-[#14161f] border-[#222634] text-slate-300 hover:border-slate-600'"
            @click="modelValue.textTransform = modelValue.textTransform === 'uppercase' ? 'none' : 'uppercase'"
          >
            {{ modelValue.textTransform === 'uppercase' ? 'SEMUA BESAR' : 'Normal' }}
          </button>
        </div>
      </div>

      <!-- Colors (Text & Outline) -->
      <div class="grid grid-cols-2 gap-2.5">
        <!-- Text Color -->
        <div class="flex flex-col gap-1.5">
          <span class="text-[10px] font-mono text-slate-400 font-bold uppercase">Warna Teks</span>
          <div class="flex items-center gap-2 bg-[#090b0e] p-1.5 rounded-md border border-[#212532]">
            <input
              type="color"
              v-model="modelValue.textColor"
              class="w-6 h-6 rounded cursor-pointer bg-transparent border-0 p-0"
            />
            <span class="font-mono text-[10px] text-slate-200 uppercase font-bold">{{ modelValue.textColor }}</span>
          </div>
        </div>

        <!-- Outline Color -->
        <div class="flex flex-col gap-1.5">
          <span class="text-[10px] font-mono text-slate-400 font-bold uppercase">Warna Outline</span>
          <div class="flex items-center gap-2 bg-[#090b0e] p-1.5 rounded-md border border-[#212532]">
            <input
              type="color"
              v-model="modelValue.outlineColor"
              class="w-6 h-6 rounded cursor-pointer bg-transparent border-0 p-0"
            />
            <span class="font-mono text-[10px] text-slate-200 uppercase font-bold">{{ modelValue.outlineColor }}</span>
          </div>
        </div>
      </div>

      <!-- Quick Color Palette Swatches -->
      <div class="flex items-center justify-between px-1">
        <span class="text-[10px] text-slate-500 font-mono">Swatches:</span>
        <div class="flex items-center gap-1.5">
          <button
            v-for="c in ['#FFE600', '#FFFFFF', '#00F2FE', '#10B981', '#F43F5E', '#000000']"
            :key="c"
            class="w-4 h-4 rounded-full border border-black/40 cursor-pointer transform hover:scale-110 transition-transform"
            :style="{ backgroundColor: c }"
            @click="modelValue.textColor = c"
            :title="`Pilih warna ${c}`"
          />
        </div>
      </div>

      <!-- Outline Stroke Width -->
      <div class="flex flex-col gap-1.5">
        <div class="flex justify-between items-center text-[10px] font-mono text-slate-400 font-bold uppercase">
          <span>Ketebalan Stroke (Outline)</span>
          <span class="text-[#ffb800]">{{ modelValue.outlineWidth }}px</span>
        </div>
        <input
          type="range"
          min="0"
          max="8"
          v-model.number="modelValue.outlineWidth"
          class="range range-xs studio-slider cursor-pointer"
        />
      </div>

      <!-- Box Background -->
      <div class="p-2.5 rounded-lg bg-[#0e1016] border border-[#1e222f] flex flex-col gap-2.5">
        <span class="text-[10px] font-mono text-slate-400 font-bold uppercase">Background Kotak</span>
        <div class="grid grid-cols-2 gap-2">
          <div class="flex items-center gap-1.5 bg-[#090b0e] p-1 rounded border border-[#222634]">
            <input
              type="color"
              v-model="modelValue.bgColor"
              class="w-5 h-5 rounded cursor-pointer bg-transparent border-0 p-0"
            />
            <span class="font-mono text-[10px] text-slate-300 uppercase">{{ modelValue.bgColor }}</span>
          </div>
          <div class="flex flex-col justify-center gap-0.5">
            <div class="flex justify-between text-[9px] font-mono text-slate-400">
              <span>Opasitas</span>
              <span class="text-[#ffb800] font-bold">{{ Math.round(modelValue.bgOpacity * 100) }}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              v-model.number="modelValue.bgOpacity"
              class="range range-xs studio-slider cursor-pointer"
            />
          </div>
        </div>
      </div>

      <!-- Vertical Position Slider -->
      <div class="flex flex-col gap-1.5">
        <div class="flex justify-between items-center text-[10px] font-mono text-slate-400 font-bold uppercase">
          <span>Posisi Vertikal Caption</span>
          <span class="text-[#ffb800]">{{ modelValue.positionY }}%</span>
        </div>
        <input
          type="range"
          min="20"
          max="88"
          v-model.number="modelValue.positionY"
          class="range range-xs studio-slider cursor-pointer"
        />
        <div class="flex justify-between text-[9px] font-mono text-slate-500 pt-0.5">
          <button class="hover:text-slate-300 cursor-pointer" @click="modelValue.positionY = 25">Atas (25%)</button>
          <button class="hover:text-slate-300 cursor-pointer" @click="modelValue.positionY = 50">Tengah (50%)</button>
          <button class="text-[#ffb800] font-bold cursor-pointer" @click="modelValue.positionY = 78">Bawah Viral (78%)</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const props = defineProps({
  modelValue: {
    type: Object,
    required: true,
  },
});

const activePresetId = ref('tiktok');

const presets = [
  {
    id: 'tiktok',
    name: 'TikTok Viral',
    sub: 'Kuning Bold',
    config: {
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
    },
  },
  {
    id: 'reels',
    name: 'Reels Clean',
    sub: 'Putih Minimal',
    config: {
      fontFamily: 'Inter, sans-serif',
      fontSize: 24,
      textColor: '#FFFFFF',
      outlineColor: '#000000',
      outlineWidth: 0,
      shadowColor: '#000000',
      shadowDepth: 0,
      bgColor: '#000000',
      bgOpacity: 0.65,
      positionY: 80,
      isBold: true,
      textTransform: 'none',
      highlightActiveWord: false,
      highlightColor: '#FFE600',
    },
  },
  {
    id: 'shorts',
    name: 'YT Shorts',
    sub: 'Drop Shadow',
    config: {
      fontFamily: 'Montserrat, sans-serif',
      fontSize: 26,
      textColor: '#FFFFFF',
      outlineColor: '#000000',
      outlineWidth: 2,
      shadowColor: '#000000',
      shadowDepth: 3,
      bgColor: '#000000',
      bgOpacity: 0.0,
      positionY: 82,
      isBold: true,
      textTransform: 'none',
      highlightActiveWord: false,
      highlightColor: '#00F2FE',
    },
  },
];

function applyPreset(preset) {
  activePresetId.value = preset.id;
  Object.assign(props.modelValue, preset.config);
}

function resetToDefault() {
  applyPreset(presets[0]);
}
</script>

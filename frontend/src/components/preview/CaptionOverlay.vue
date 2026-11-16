<template>
  <div
    v-if="currentText"
    class="absolute inset-x-0 pointer-events-none flex justify-center px-4 transition-all duration-75 select-none"
    :style="containerStyle"
  >
    <div
      class="max-w-[90%] text-center leading-snug px-3 py-1.5 rounded transition-all flex flex-wrap justify-center items-center gap-x-1.5 gap-y-1"
      :style="textStyle"
    >
      <!-- Word-by-Word Highlight Mode (Karaoke / Dynamic effect) -->
      <template v-if="styleConfig.highlightActiveWord && currentWords && currentWords.length > 0">
        <span
          v-for="(w, idx) in currentWords"
          :key="idx"
          class="inline-block transition-transform duration-100"
          :style="getWordStyle(w)"
        >
          {{ formatWord(w.word) }}
        </span>
      </template>

      <!-- Standard Line Text Mode -->
      <template v-else>
        {{ formattedText }}
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  currentText: {
    type: String,
    default: '',
  },
  currentWords: {
    type: Array,
    default: () => [],
  },
  currentTime: {
    type: Number,
    default: 0,
  },
  styleConfig: {
    type: Object,
    default: () => ({
      fontFamily: 'Montserrat, sans-serif',
      fontSize: 28,
      textColor: '#FFFFFF',
      highlightColor: '#00F2FE',
      highlightActiveWord: true,
      outlineColor: '#000000',
      outlineWidth: 3,
      shadowColor: '#000000',
      shadowDepth: 2,
      bgColor: '#000000',
      bgOpacity: 0.0,
      positionY: 82,
      isBold: true,
      textTransform: 'none',
    }),
  },
});

function formatWord(w) {
  if (!w) return '';
  return props.styleConfig.textTransform === 'uppercase' ? w.toUpperCase() : w;
}

const formattedText = computed(() => {
  if (!props.currentText) return '';
  if (props.styleConfig.textTransform === 'uppercase') {
    return props.currentText.toUpperCase();
  }
  return props.currentText;
});

const containerStyle = computed(() => {
  return {
    top: `${props.styleConfig.positionY}%`,
    transform: 'translateY(-50%)',
  };
});

function getWordStyle(w) {
  const isCurrent = props.currentTime >= w.start && props.currentTime <= w.end;
  if (isCurrent) {
    return {
      color: props.styleConfig.highlightColor || '#00F2FE',
      transform: 'scale(1.12)',
      textShadow: `0 0 10px ${props.styleConfig.highlightColor || '#00F2FE'}80`,
    };
  }
  return {};
}

const textStyle = computed(() => {
  const cfg = props.styleConfig;
  const hexBg = cfg.bgColor || '#000000';
  const r = parseInt(hexBg.slice(1, 3) || '0', 16);
  const g = parseInt(hexBg.slice(3, 5) || '0', 16);
  const b = parseInt(hexBg.slice(5, 7) || '0', 16);
  const bgRgba = `rgba(${r}, ${g}, ${b}, ${cfg.bgOpacity})`;

  return {
    fontFamily: cfg.fontFamily,
    fontSize: `${cfg.fontSize}px`,
    color: cfg.textColor,
    fontWeight: cfg.isBold ? '800' : '500',
    backgroundColor: cfg.bgOpacity > 0 ? bgRgba : 'transparent',
    WebkitTextStroke: cfg.outlineWidth > 0 ? `${cfg.outlineWidth}px ${cfg.outlineColor}` : 'none',
    textShadow: cfg.shadowDepth > 0 ? `${cfg.shadowDepth}px ${cfg.shadowDepth}px ${cfg.shadowDepth * 2}px ${cfg.shadowColor}` : 'none',
  };
});
</script>

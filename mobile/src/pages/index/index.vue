<template>
  <view class="index">
    <Counter />
  </view>
  <view>
    <text>aaa</text>
  </view>
</template>

<script>
import './index.css'
import Counter from '../../components/Counter.vue'

export default {
  name: 'index',
  components: {
    Counter
  }
}
</script>

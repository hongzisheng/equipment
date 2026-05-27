<template>
  <view>
    This is a Notifications View
  </view>
</template>

<script setup lang="ts">
import Taro, {useDidShow} from "@tarojs/taro";

const requestSubscriptions = () => {

}
useDidShow(requestSubscriptions)
</script>

<style>

</style>

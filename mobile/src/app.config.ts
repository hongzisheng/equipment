export default {
  pages: [
    'pages/home/home',
    'pages/schedule/schedule',
    'pages/scheduleDetails/scheduleDetails',
    'pages/record/record',
    'pages/mine/mine',
    'pages/login/login',
    'pages/progress/progress',
    'pages/notifications/notifications',

  ],
  window: {
    backgroundTextStyle: 'light',
    navigationBarBackgroundColor: '#fff',
    navigationBarTitleText: '石化设备大检修系统',
    navigationBarTextStyle: 'black'
  },
  tabBar: {
    color: "#666",
    selectedColor: "#3EBD97",
    backgroundColor: "#ffffff",
    borderStyle: "black",
    list: [
      {
        pagePath: "pages/home/home",
        text: "首页",
        iconPath: "assets/navigateBarIcons/home.png",
        selectedIconPath: "assets/navigateBarIcons/home-active.png"
      },
      {
        pagePath: "pages/schedule/schedule",
        text: "日程",
        iconPath: "assets/navigateBarIcons/schedule.png",
        selectedIconPath: "assets/navigateBarIcons/schedule-active.png"
      },
      {
        pagePath: "pages/record/record",
        text: "记录",
        iconPath: "assets/navigateBarIcons/record.png",
        selectedIconPath: "assets/navigateBarIcons/record-active.png"
      },
      {
        pagePath: "pages/mine/mine",
        text:"我的",
        iconPath: "assets/navigateBarIcons/user.png",
        selectedIconPath: "assets/navigateBarIcons/user-active.png"
      }
    ]
  },
}

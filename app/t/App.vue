<script>
	export default {
		onLaunch: function() {
			console.log('App Launch')
			// 检查是否有已登录用户
			const userInfo = uni.getStorageSync('userInfo');
			if (!userInfo) {
				// 如果没有登录，跳转到身份选择页面
				uni.reLaunch({ url: '/pages/identity/select' });
			}
		},
		onShow: function() {
			console.log('App Show')
		},
		onHide: function() {
			console.log('App Hide')
		}
	}
</script>

<style>
	/*每个页面公共css */
	* {
		margin: 0;
		padding: 0;
		box-sizing: border-box;
	}
	
	body {
		font-family: Arial, sans-serif;
	}
</style>

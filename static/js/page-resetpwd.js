$(document).ready(function() {

	$("#newpwd").blur(function() {
		var pwd = $("#password").val();
		var cpwd = $("#confirmpwd").val();
		var reg = /^(?![0-9]+$)(?![a-zA-Z]+$)[0-9A-Za-z]{6,16}$/;
		if (pwd !== cpwd) {
			$("#tip2").css({
				"display": "inline-block"
			})
		} else {
			$("#tip2").css({
				"display": "none"
			})
		}
		if (reg.test(pwd)) {
			$("#tip1").css({
				"display": "none"
			})
		} else {
			$("#tip1").css({
				"display": "inline-block"
			})
		}
		
	})

	$("#confirmpwd").blur(function() {
		var pwd = $("#password").val();
		var cpwd = $("#confirmpwd").val();
		var reg = /^(?![0-9]+$)(?![a-zA-Z]+$)[0-9A-Za-z]{6,16}$/;
		if (pwd !== cpwd) {
			$("#tip2").css({
				"display": "inline-block"
			})
		} else {
			$("#tip2").css({
				"display": "none"
			})
		}
		if (reg.test(pwd)) {
			$("#tip1").css({
				"display": "none"
			})
		} else {
			$("#tip1").css({
				"display": "inline-block"
			})
		}
		
	})

	var myReg = /^(\w|(\.\w+))+@([a-zA-Z0-9_-]+\.)+(com|org|cn|net)+$/;


	$("#rebtn").click(function() {
		var password = $("#password").val();
		var username = $("#username").val();
		var cpwd = $("#confirmpwd").val();
 
 
		if (!username) {
			alert("请输入账号!");
			$("#username").focus();
			return;
		}
		if (!password) {
			alert("请输入密码!");
			$("#password").focus();
			return;
		}
		if (!cpwd) {
			alert("请输入确认密码!");
			$("#cpwd").focus();
			return;
		}
		
		console.log("username:" + username);
		console.log("password:" + password);
		

		
		
		var reg = /^(?![0-9]+$)(?![a-zA-Z]+$)[0-9A-Za-z]{6,16}$/;
		if (reg.test(password) && password) {
			$.post("/moduser", {
			
				"username": username,
				"password": password

			}, function(data) {

					alert("重设密码成功");
					window.location.href = "reotherpwd.html";

			
			}, 'json')
		} else {
			alert("请更正")
			return false;
		}
	})

});

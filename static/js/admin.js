$(document).ready(function () {
    $.post('/teacher/countteacher',
        null,
        function (data1) {
			        document.getElementById("teachernum").innerText = data1;
           console.log("teachernum:"+data1)
	
		
		$.post('/student/countstudent',
		    null,
		    function (data) {
				        document.getElementById("studentnum").innerText = data;
		       console.log("studentnum:"+data)
		document.getElementById("totalnum").innerText = data1+data;
		    },
		    'json'
		)
		
        },
        'json'
    )
	
	

	
})
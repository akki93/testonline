$(document).ready(function(){

	

    $("form").on('submit' , function(event){
        // alert("form has been submit");
        $.ajax({
        	data:{
        		exam_name:$('#exam_name').val()
        	},
        	type:'POST',
        	url : '/control-center/exam_created'
        })
        .done(function(data){
        	if (data.error){
        		$('#sucess_message').text(data.error).show();

        	}
        	else if (data.sucess_submit){
        		// alert(sucess_submit);
        		$('#sucess_message').text(data.sucess_submit).show();
        		// $("#all-exam").trigger("click")
        		$('#sucess_message').delay(3000).fadeOut();
        		$('#form_exam_add').delay(3000).fadeOut();


        	}
        	else{
        		$('#sucess_message').show();
        		$('#form_exam_add').delay(1000).fadeOut();
        	}
        });
        event.preventDefault();
    });
});
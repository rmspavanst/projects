<%@ taglib prefix="form" uri="http://www.springframework.org/tags/form" %> 
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core"%>
<html>
<head>
<title>
Registration
</title>
</head>
<body>
<table>
<tr><td> </td></tr>
<h1>Participant Registration</h1>
</table>
<table>
<tr><td> </td></tr>
<c:if test="${not empty submissionmsg}">
<tr>
<td>
<c:out value="${submissionmsg}"></c:out>
</td>
</tr>
<tr><td> </td></tr>
</c:if>
</table>
<table>
<form:form action="submission" modelAttribute="memberdetails">
<tr><td><form:label path="uname">User Name :</form:label></td>
<td><form:input path="uname" maxlength="30"/></td></tr>
<tr><td><form:label path="password">Password :</form:label></td>
<td><form:input path="password" maxlength="30"/></td></tr>
<tr><td><form:label path="email">Email :</form:label></td>
<td><form:input path="email" maxlength="30"/></td></tr>
<tr><td><form:label path="phone">Phone Number :</form:label></td>
<td><form:input path="phone" maxlength="10"/></td></tr>
<tr><td> </td></tr><tr><td> </td></tr>
<tr><td> </td></tr><tr><td> </td></tr>
<tr><td><form:button value="submit">submit</form:button></td>


<!-- 
<td><form:button value="list">list</form:button></td></tr>
 -->
</form:form>

<form:form action="showList" modelAttribute="memberdetails">
<tr><td> </td></tr><tr><td> </td></tr>
<tr><td> </td></tr><tr><td> </td></tr>
<tr><td><form:button value="submit">Participant List</form:button></td> 
</form:form>
</table>
<br><br>
<c:if test="${not empty memlist}">
<table border="1">
<tr>
<th>User Name</th>
<th>Password</th>
<th>Email</th>
<th>Phone</th>
</tr>
<c:forEach items="${memlist}" var="lists">
<tr><td>${lists.uname}</td>
<td>${lists.password}</td>
<td>${lists.email}</td>
<td>${lists.phone}</td></tr>    
</c:forEach>
</table>
</c:if>
<script>
function showList() {
$.ajax({
	  alert('test');
	  url: "showList", //or setJSP.jsp
	  alert('test1');
	  success: function(){
	    alert ('ok');
	  }
	});
}	

</script>
</body>
</html>
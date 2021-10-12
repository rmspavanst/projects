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
<form:form action="submission" modelAttribute="memberdetails">
<tr><td><form:label path="uname">User Name :</form:label></td>
<td><form:input path="uname"/></td></tr>
<tr><td><form:label path="password">Password :</form:label></td>
<td><form:input path="password"/></td></tr>
<tr><td><form:label path="email">Email :</form:label></td>
<td><form:input path="email"/></td></tr>
<tr><td><form:label path="phone">Phone Number :</form:label></td>
<td><form:input path="phone"/></td></tr>
<tr><td><form:button value="submit">submit</form:button></td>
<td><form:button value="submit">list</form:button></td></tr>
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
</body>
</html>

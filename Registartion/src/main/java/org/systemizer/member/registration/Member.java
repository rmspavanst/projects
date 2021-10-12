package org.systemizer.member.registration;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.Table;

@Entity
@Table(name = "member")
public class Member 
{
	@Id
	@Column(name = "uname")
	private String uname;
	@Column(name = "password")
	private String password; 
	@Column(name = "email")
	private String email; 
	@Column(name = "phone")
	private String phone;

	public String getUname() {
		return uname;
	}

	public void setUname(String uname) {
		this.uname = uname;
	}

	public String getPassword() {
		return password;
	}

	public void setPassword(String password) {
		this.password = password;
	}

	public String getEmail() {
		return email;
	}

	public void setEmail(String email) {
		this.email = email;
	}

	public String getPhone() {
		return phone;
	}

	public void setPhone(String phone) {
		this.phone = phone;
	}

	public void addAttribute(String string, String string2) {
				
	}
	
	

}

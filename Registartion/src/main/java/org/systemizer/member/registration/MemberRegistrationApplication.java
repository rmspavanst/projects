package org.systemizer.member.registration;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.boot.web.servlet.support.SpringBootServletInitializer;

@SpringBootApplication
public class MemberRegistrationApplication extends SpringBootServletInitializer
{

	  public static void main(String[] args) {
	  SpringApplication.run(MemberRegistrationApplication.class, args); 
	  }
	  
	  @Override protected SpringApplicationBuilder
	  configure(SpringApplicationBuilder builder) { 
	  return builder.sources(MemberRegistrationApplication.class); }
	 
	
	

}

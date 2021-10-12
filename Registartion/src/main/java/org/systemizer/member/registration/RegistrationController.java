package org.systemizer.member.registration;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.servlet.ModelAndView;

@Controller
public class RegistrationController 
{
	@Autowired
	private RegistrationRepository registrationRepo;
	
	@GetMapping(value = {"/registration"})
	public ModelAndView registration(@ModelAttribute("memberdetails") Member member)
	{
		return new ModelAndView("memberRegistration");
	}
	/*
	 * @PostMapping(value = {"/submission"}) public ModelAndView
	 * registerMember(@ModelAttribute("memberdetails") Member member) {
	 * registrationRepo.save(member); ModelAndView modelView=new
	 * ModelAndView("memberRegistration"); return modelView.addObject("memlist",
	 * registrationRepo.findAll()); }
	 */
	
	@PostMapping(value = {"/submission"})
	public ModelAndView registerMember(@ModelAttribute("memberdetails") Member member) 
	{
		ModelAndView modelView=new ModelAndView("memberRegistration");
		if(member.getUname().equalsIgnoreCase("")||
				member.getPassword().equalsIgnoreCase("")||
				member.getEmail().equalsIgnoreCase("")||
				member.getPhone().equalsIgnoreCase("")) {
			modelView.addObject("submissionmsg", "Please enter valid/correct member details");
		}
		else {
		registrationRepo.save(member);
		modelView.addObject("submissionmsg", "Member Registered Successfully");
		}
		 // return modelView.addObject("memlist", registrationRepo.findAll());
		 return modelView;
	}
	

	@PostMapping(value = {"/showList"})
	public ModelAndView List(@ModelAttribute("memberdetails") Member member) 
	{
		
	    ModelAndView modelView=new ModelAndView("memberRegistration");
		return modelView.addObject("memlist", registrationRepo.findAll());
		 
	}

}

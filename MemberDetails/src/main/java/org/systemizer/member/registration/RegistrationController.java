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
	public void registerMember(@ModelAttribute("memberdetails") Member member) 
	{
		registrationRepo.save(member);
	    @SuppressWarnings("unused")
		ModelAndView modelView=new ModelAndView("memberRegistration");
		 // return modelView.addObject("memlist", registrationRepo.findAll());
		 
	}
	

	@PostMapping(value = {"/showList"})
	public ModelAndView List(@ModelAttribute("memberdetails") Member member) 
	{
		
	    ModelAndView modelView=new ModelAndView("memberRegistration");
		return modelView.addObject("memlist", registrationRepo.findAll());
		 
	}

}

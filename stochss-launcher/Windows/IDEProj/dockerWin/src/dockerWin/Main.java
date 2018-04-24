package dockerWin;

import java.awt.Desktop;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.net.URI;
import java.net.URISyntaxException;

import javax.swing.SwingWorker;

/**
 * 
 *
 */
public class Main {
	static final boolean debug = true;
	
	
	private String containerName = "stochsscontainer1_9";
	private String VMname = "stochss1-9";
	private String imageName = "stochss/stochss-launcher:1.9";
	private int logLimit = 100;
	private boolean toolbox = false;
	
	private String ip = "127.0.0.1";
	private String url;
	
	private final String finishedStr = "---finished---";
	
	private final String commands[] = {
	/*0*/ "docker ps -a -f name=" + containerName, 								//search for container of container name
	/*1*/ "docker pull " + imageName, 											//download image
	/*2*/ "docker start " + containerName,										//start container
	/*3*/ "docker exec -i " + containerName + " /bin/bash -c \"cd " +
				"stochss-master && ./run.ubuntu.sh -a 0.0.0.0 -t secretkey\"", 	//run StochSS
	/*4*/ "docker stop " + containerName,										//stop container
	/*5*/ "echo " + finishedStr,												//arbitrary echo to tell if operation is over
	/*6*/ "docker rm " + containerName,											//uninstall container
	/*7*/ "docker rmi stochss/stochss-launcher:1.9",							//uninstall image
	/*8  - Toolbox*/ "docker-machine rm " + VMname,								//uninstall VM
	/*9*/ "docker create -t -p 9999:9999 -p 8080:8080 --name=" + containerName + " " + imageName, //create container
	/*10*/ 
	/*11*/
	/*12*/
	};
	
	private ProcessBuilder builder;
	
	private Process process;
	private BufferedWriter stdin;
	private BufferedReader stdout;
	
	private UIHandler window;
	private Process subp;
	private String toolbox1, toolbox2, toolboxPath;
	
	public Main(UIHandler w) {
		window = w;
		builder = new ProcessBuilder("cmd");
	}
	
	public void initialize() {
		try { 
			process = builder.start();
		} catch (IOException e) {
			log(e, true);
		}
	    stdin = new BufferedWriter(new OutputStreamWriter(process.getOutputStream()));
	    stdout = new BufferedReader(new InputStreamReader(process.getInputStream()));
	    if (checkToolbox()) {
	    	toolbox = true;
	    	try {
				enterToolbox(stdin, stdout, process);
			} catch (IOException e) {
				log(e, true);
			}
	    }
	}
	
	private boolean checkToolbox() {
		//TODO
		return true;
	}

	public void uninstall() throws IOException {
		SwingWorker<Boolean, String> worker = new SwingWorker<Boolean, String>() {
			 @Override
			 protected Boolean doInBackground() throws IOException {
				 String line;
				 stdin.write(commands[6]); 
				 stdin.newLine();
				 stdin.write(commands[7]);
				 stdin.newLine();
				 stdin.write(commands[5]);
				 stdin.newLine();
				 stdin.flush();
				 while((line = stdout.readLine()) != null && !line.contains(commands[5])) { 
				    window.addText(line);
				}
				if (toolbox) {} //TODO
				return true;
			  }
			  @Override
			  protected void done() {
			    window.setUninstallDone();
			  }
			};
		worker.execute();
	}
	/**
	 * This function checks if StochSS is installed. 
	 * @return boolean whether or not stochss is installed
	 * @throws IOException
	 */
	public boolean checkIfInstalled() throws IOException {
		String line;
	    
		terminalWrite(commands[0],commands[5],stdin); 
	    
		while((line = stdout.readLine()) != null && !(line.contains(finishedStr) && !line.contains(commands[5]))) { 
	    	window.addText(line);
	    	if (line.contains(containerName) && !line.contains(commands[0])) {
	    		window.setStartup();
	    		if(debug) {System.out.println("checkIfInstalled returns true");}
	    		return true;
	    	}
	    }
		if(debug) {System.out.println("checkIfInstalled returns false");}
	    return false;
	}
	
	public boolean checkIfVMInstalled() throws IOException {
		String line;

		terminalWrite("docker-machine ls",commands[5],stdin);
		/*
		 * !(A && !B)

		 *	!A + B
		 */
		while((line = stdout.readLine()) != null && !(line.contains(finishedStr) && !line.contains(commands[5]))) { 
	    	window.addText(line);
	    	if (line.contains(VMname)) {
	    		if(debug) {System.out.println("Check if vm installed: true");}
	    		return true;
	    	}
	    }
		if(debug) {System.out.println("Check if vm installed: false");}
		return false;
	}
	
	public void startVM() throws IOException {
		SwingWorker<Boolean, String> worker = new SwingWorker<Boolean, String>() {
			 @Override
			 protected Boolean doInBackground() throws IOException {
				 String line;
				 
				 terminalWrite("docker-machine start stochss1-9",commands[5],stdin);
				 
				 if(debug) { System.out.println("docker-machine start stochss1-9"); }
				 
				 while((line = stdout.readLine()) != null && !(line.contains(finishedStr) && !line.contains(commands[5]))) { 
					 if(debug) {System.out.println(line);}
					 window.addText(line);
				 }
				 
				 if(debug) { System.out.println("eval \"$(docker-machine env stochss1-9)\""); }
				 
				 terminalWrite("eval \"$(docker-machine env stochss1-9)\"",commands[5],stdin);
				 
				 while((line = stdout.readLine()) != null && !(line.contains(finishedStr) && !line.contains(">"))) { 
					 window.addText(line);
				 }
				if(debug) {System.out.println("StartVM returns true");}
				return true;
			  }
			  @Override
			  protected void done() {
				try {
					if (checkIfInstalled()) {
						window.setStartup();
					} else {
						window.setnotInstall();
					}
				} catch (IOException e) {
					log(e, true);
				}
			  }
			};
		worker.execute();
	}
	
	public void install() throws IOException {
		SwingWorker<Boolean, String> worker = new SwingWorker<Boolean, String>() {
			 @Override
			 protected Boolean doInBackground() throws IOException {
				String line;
				stdin.write(commands[1]);
				stdin.newLine();
				stdin.flush();
				while((line = stdout.readLine()) != null && !line.startsWith("Status: ")) {
				 	window.addText(line);
				}
				window.addText(line);
				stdin.write(commands[9]);
				stdin.newLine();
				stdin.flush();
				window.addText(stdout.readLine());
				return true;
			  }
			  @Override
			  protected void done() {
				try {
					if (checkIfInstalled()) {
						window.setStartup();
					} else {
						log("Installation Failed", true);
					}
				} catch (IOException e) {
					log(e, true);
				}
			  }
			};
		worker.execute();		
	}
	    
	public void startStochSS() throws IOException {
		SwingWorker<Boolean, String> worker = new SwingWorker<Boolean, String>() {
			 @Override
			 protected Boolean doInBackground() throws IOException {
				 String line;
				 stdin.write(commands[2]);
				 stdin.newLine();
				 stdin.write(commands[3]);
				 stdin.newLine();
				 stdin.flush();
				 while((line = stdout.readLine()) != null && !line.startsWith("Navigate to ")) {
				 	window.addText(line);
				}
				 try {
				   	url = line.substring(12, line.indexOf(" to access StochSS"));
				   	if(url.contains("0.0.0.0")) {
				   		int temp = url.indexOf("0.0.0.0");
				   		url = url.substring(0, temp) + ip + url.substring(temp + 7);
				   	}
				   	window.addText("Navigate to " + url + " to access StochSS");
				   	return true;
				 } catch (Exception e) {
				   	log(e, true);
				   	return false;
				 }
			  }
			  @Override
			  protected void done() {
			    window.setRunning();
			  }
			};
		worker.execute();
	}
	    
	public boolean openURL() {
		if (Desktop.isDesktopSupported()) {
	    	try {
				Desktop.getDesktop().browse(new URI(url));
				return true;
			} catch (URISyntaxException | IOException e) {
				log(e, false);
				return false;
			}
		}
		return false;
	}
		
	public void safeExit() throws IOException { //TODO: if any of these hang, need to detect it and destroyProcesses that way
		subp = builder.start();	
		BufferedWriter exitin = new BufferedWriter(new OutputStreamWriter(subp.getOutputStream()));
	    BufferedReader exitout = new BufferedReader(new InputStreamReader(subp.getInputStream()));
	    if (toolbox) { 
	    	enterToolbox(exitin, exitout, subp); 
	    }
	    String line;
	    exitin.write(commands[4]);
	    exitin.newLine();
	    exitin.write(commands[5]);
	    exitin.newLine();
	    exitin.flush();
	    while((line = exitout.readLine()) != null && !line.contains(commands[5])) {  //[1]
	    	window.addText(line); 
		}
		destroyProcesses();
		// [1] For some reason this hangs if changed to the !(line.contains(commands[5]) && !line.contains(">")) version, 
		//which is supposed to be MORE robust/less error-prone than !line.contains(commands[5])
	}
	
	private void destroyProcesses() {
		if (process != null) 
			process.destroy();
		if (subp != null)
			subp.destroy();
	}
	
	public void log(Exception e, boolean exit) {
		String s = "";
		StringWriter errors = new StringWriter();
		e.printStackTrace(new PrintWriter(errors));
		s += errors.toString(); 
		log(s, exit);
	}
	
	public boolean getToolbox() {
		return toolbox;
	}
	
	public void log(String str, boolean exit) {
		if(exit) {
			try {
				safeExit();
			} catch (Exception ex) {
				str += "\nSafe exit failed.\n";
				destroyProcesses();
			} finally {
				window.setStopped();
			}
		}
//		try {
//			//TODO saveLog(window.getWindowText() + "\n\r" + str);
//		} catch (FileNotFoundException e) {
//			str += "\nLog file creation failed.\n";
//		}
		window.addText(str);
	}

	public String getURL() {
		return url;
	}
	
	private void enterToolbox(BufferedWriter in, BufferedReader out, Process p) throws IOException {
		String line;
		if (toolboxPath == null) {
//			/"C:\Program Files\Git\bin\bash.exe" --login -i "C:\Program Files\Docker Toolbox\start.sh"
			
			terminalWrite("where docker",commands[5],in);
			
			while((line = out.readLine()) != null && !(line.contains(finishedStr) && !line.contains(commands[5]))) {  
		    	window.addText(line);
		    	if (line.contains("Docker Toolbox")) {
		    		toolbox1 = line.substring(0, line.indexOf("docker.exe"));
		    		break;
		    	}
		    }
			
			terminalWrite("where git",commands[5],in);
			
			
			while((line = out.readLine()) != null && !(line.contains(finishedStr) && !line.contains(commands[5]))) {  
		    	window.addText(line);
		    	if (line.contains("cmd\\git.exe")) {
		    		toolbox2 = line.substring(0, line.indexOf("cmd\\git.exe"));
		    		break;
		    	}
		    }
			toolboxPath = "\"" + toolbox2 + "bin\\bash.exe\" --login -i \"" + toolbox1 + "start.sh\"";
		}		
		
		terminalWrite(toolboxPath,commands[5],in);
		
		
		while((line = out.readLine()) != null && !(line.contains(finishedStr) && !line.contains(commands[5]))) {  
	    	window.addText(line);
	    }
		System.out.println(toolbox1 + " " + toolbox2 + " " + toolboxPath);
			
		/* TODO
		 * where docker 
			> save "docker toolbox" up to "docker.exe" then replace with "start.sh"

			where git
			> save up to "cmd\git.exe" and replace with "bin\bash.exe"

			cd var 1, ending at "\start.sh"
			"var2" -login -i "var1"
		 */
	}
	/**
	 * 
	 * @param command
	 * @param in
	 * @throws IOException
	 */
	private void terminalWrite(String command,BufferedWriter in) throws IOException{
		in.write(command);
		in.newLine();
		in.flush();
	}
	/**
	 * 
	 * @param command1
	 * @param command2
	 * @param in
	 * @throws IOException
	 */
	private void terminalWrite(String command1, String command2, BufferedWriter in) throws IOException{
		in.write(command1 + " && " + command2);
		in.newLine();
		in.flush();
	}

}


/* docker ps -f stochsscontainer1_9
 * if no docker command found -> 'please install docker'
 * if 'error' -> docker shortcut
 * if not exist -> install(container)
 * if exit -> start container/run StochSS
 * 
 * docker shortcut -> check if stochss1-9 exists, if not test HyperV/VirtualBox using test environ, install(HyperV/VirtualBox)
 * 							if stochss1-9 exists, follow commands to start, grab url, test for container exist
 * 													if exist -> start container/run StochSS
 * 													if not exist -> install(container)
 * 
 * install -> run install instructions, restart program checks
 * proceed with start -> one line run container grab url
 * 
 * close -> if toolbox, spin up another quickstart terminal if not cmd
 * run closing checks */

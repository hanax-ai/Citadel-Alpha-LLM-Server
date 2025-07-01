CodeRabbit
Shell glob may remove unintended packages

apt remove --purge nvidia* will let the shell expand nvidia* to filenames in the current directory if any exist, leading to unpredictable behaviour.
Safer pattern:

-sudo apt remove --purge nvidia* -y
+sudo apt-get -y remove --purge '^nvidia.*'
Quote the pattern so the shell doesn’t expand it and use apt-get for non-interactive scripting.


CodeRabbit
Over-writing /etc/environment nukes existing variables

The tee /etc/environment block replaces the whole file, potentially discarding proxies, locale, or custom vars. Append or surgically edit instead:

sudo sed -i '/^PATH=/d' /etc/environment
echo "PATH=\"${CURRENT_PATH}:${CUDA_PATH}/bin\"" | sudo tee -a /etc/environment
Preserves everything else while injecting the CUDA paths.

CodeRabbit
GPU optimisation only targets GPU 0

nvidia-smi -pl and -ac without -i act on GPU 0, leaving the second card untouched. Loop over all GPUs:

GPU_COUNT=$(nvidia-smi -L | wc -l)
for idx in $(seq 0 $((GPU_COUNT-1))); do
    nvidia-smi -i "$idx" -pl "$POWER_LIMIT" || echo "⚠️  power-limit GPU$idx"
    nvidia-smi -i "$idx" -ac "${MAX_MEM_CLOCK},${MAX_GR_CLOCK}" || true
done

CodeRabbit
Static port resurfaced – update print statement again

The earlier fix correctly parameterised the docs URL, yet this later block still prints the hard-coded 8000.
For consistency and to avoid stale URLs, interpolate port here as well.

-        print("📚 API docs at: http://localhost:8000/docs")
+        print(f"📚 API docs at: http://localhost:{port}/docs")

CodeRabbit
tune2fs is executed on the whole disk, not the partition

/dev/nvme1n1 is the disk; the filesystem lives on a partition (e.g. /dev/nvme1n1p1).
Running tune2fs on the block device without a super-block will fail.

Capture the partition via findmnt -nro SOURCE --target /mnt/citadel-models before calling tune2fs.

CodeRabbit
Secondary-NVMe detection is unreliable on LVM systems

lsblk "$device" | grep -q "/boot\|/$" only sees mount-points on raw devices, not on the LVM partitions created on nvme0n1.
On a system that follows the layout in the same document (nvme0n1p3 → ubuntu-vg), the primary NVMe /dev/nvme0n1 is not mounted and will therefore be mis-detected as the free “model” drive. A wrong drive will then be reformatted, tuned and trimmed.

Consider:

- for device in /dev/nvme*n1; do
-     if [ -b "$device" ] && ! mount | grep -q "$device"; then
-         if ! lsblk "$device" | grep -q "/boot\|/$"; then
+ for device in $(lsblk -ndo NAME,TYPE | awk '$2=="disk"{print "/dev/"$1}'); do
+     if [[ "$device" == /dev/nvme* ]] && \
+        ! lsblk -nro MOUNTPOINT "$device" | grep -q .; then
Please also validate against the disk UUID expected in /etc/fstab to avoid destructive mistakes.

Also applies to: 90-98

CodeRabbit
Interactive prompts will block automation

read -p "Delete and recreate? …" and similar prompts break non-interactive CI runs or Ansible/Cloud-Init executions.

Provide a --yes / --force flag or honour $CI / $DEBIAN_FRONTEND=noninteractive to keep the pipeline headless.

Also applies to: 228-235
CodeRabbit
Activation-script test passes unsupported -c option

bash /opt/citadel/scripts/activate-citadel.sh -c … will be interpreted as a positional parameter ($1="-c"), but the generated activation script does not parse options and will exit with usage errors.

Use a subshell to source the script instead:

source /opt/citadel/scripts/activate-citadel.sh && echo "Activation test passed"

CodeRabbit
python-error-handler.sh execute cannot see shell functions

$ERROR_HANDLER execute "Environment Manager Creation" "create_env_manager" … starts a new shell, so the function create_env_manager defined in the parent script is undefined there.
The exec will fail with “command not found”.

Options:

- $ERROR_HANDLER execute "Environment Manager Creation" "create_env_manager" ...
+ create_env_manager
+ $ERROR_HANDLER validate "Environment Manager Creation" "[ -f /opt/citadel/scripts/env-manager.sh ]"

The issue is that the shell function create_env_manager is not available in the subshell started by $ERROR_HANDLER execute ..., causing a "command not found" error. The best fix is to move the body of create_env_manager directly into the main script block, so it is executed inline and not as a function call.

Here is the corrected approach for that section:

Remove the function definition for create_env_manager and its call.
Inline the script creation logic directly before the error handler check.
or package the body of the function into a standalone script and call that.

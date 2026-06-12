import { useNavigate } from "react-router-dom";
import { Card, CardBody, CardFooter } from "./ui/Card";
import Badge from "./ui/Badge";
import type { ProjectResponse } from "../types/api";

interface ProjectCardProps {
  project: ProjectResponse;
}

export default function ProjectCard({ project }: ProjectCardProps) {
  const navigate = useNavigate();

  const badgeVariant =
    project.resource_type === "Patient" ? "patient" : "observation";

  const formattedDate = new Intl.DateTimeFormat("tr-TR", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(project.created_at));

  return (
    <Card hover onClick={() => navigate(`/projects/${project.id}`)}>
      <CardBody>
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <h3 className="text-base font-semibold text-slate-900 truncate">
              {project.name}
            </h3>
            {project.description && (
              <p className="mt-1 text-sm text-slate-500 line-clamp-2">
                {project.description}
              </p>
            )}
          </div>
          <Badge variant={badgeVariant}>{project.resource_type}</Badge>
        </div>
      </CardBody>
      <CardFooter className="flex items-center justify-between">
        <span className="text-xs text-slate-400">
          FHIR R4 {project.fhir_version}
        </span>
        <span className="text-xs text-slate-400">{formattedDate}</span>
      </CardFooter>
    </Card>
  );
}
